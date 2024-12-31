from __future__ import annotations

import json
from logging import getLogger
from typing import NoReturn

import requests

from payway.conf import CUSTOMER_URL, TOKEN_NO_REDIRECT, TRANSACTION_URL
from payway.constants import (
    BANK_ACCOUNT_PAYMENT_CHOICE,
    CREDIT_CARD_PAYMENT_CHOICE,
    VALID_PAYMENT_METHOD_CHOICES,
)
from payway.customers import CustomerRequest
from payway.exceptions import PaywayError
from payway.model import (
    BankAccount,
    PaymentError,
    PaymentSetup,
    PayWayCard,
    PayWayCustomer,
    PayWayPayment,
    PayWayTransaction,
    ServerError,
    TokenResponse,
)
from payway.transactions import TransactionRequest

logger = getLogger(__name__)


class Client(CustomerRequest, TransactionRequest):
    """
    PayWay Client to connect to PayWay and perform methods given credentials
    """

    merchant_id = ""
    bank_account_id = ""
    secret_api_key = ""
    publishable_api_key = ""

    def __init__(
        self,
        merchant_id: str,
        bank_account_id: str,
        secret_api_key: str,
        publishable_api_key: str,
    ) -> NoReturn:
        """
        :param merchant_id        : str                 = PayWay Merchant ID
        :param bank_account_id   : str                  = PayWay Bank Account ID
        :param secret_api_key   : str                   = PayWay Secret APi Key
        :param publishable_api_key   : str              = PayWay Publishable API Key
        """
        self._validate_credentials(
            merchant_id,
            bank_account_id,
            secret_api_key,
            publishable_api_key,
        )
        self.merchant_id = merchant_id
        self.bank_account_id = bank_account_id
        self.secret_api_key = secret_api_key
        self.publishable_api_key = publishable_api_key

        session = requests.Session()
        session.auth = (self.secret_api_key, "")
        headers = {"content-type": "application/x-www-form-urlencoded"}
        session.headers = headers
        self.session = session
        session_no_headers = requests.Session()
        session_no_headers.auth = session.auth
        self.session_no_headers = session_no_headers

    def _validate_credentials(
        self,
        merchant_id: str,
        bank_account_id: str,
        secret_api_key: str,
        publishable_api_key: str,
    ) -> NoReturn:
        if not merchant_id or not bank_account_id or not secret_api_key or not publishable_api_key:
            if not secret_api_key or not publishable_api_key:
                logger.error("PayWay API keys not found")
                raise PaywayError(
                    message="PayWay API keys not found",
                    code="INVALID_API_KEYS",
                )
            logger.error(
                "Merchant ID, bank account ID, secret API key, publishable API key are " "invalid",
            )
            raise PaywayError(
                message="Invalid credentials",
                code="INVALID_API_CREDENTIALS",
            )

    def get_request(self, endpoint: str) -> requests.Response:
        return requests.get(url=endpoint, auth=(self.secret_api_key, ""), timeout=30)

    def post_request(
        self, endpoint: str, data: dict, auth: tuple | None = None, idempotency_key: str | None = None
    ) -> requests.Response:
        """
        Supply an idempotency_key to avoid duplicate POSTs
        https://www.payway.com.au/docs/rest.html#avoiding-duplicate-posts
        """
        if not auth:
            auth = (self.secret_api_key, "")
        headers = {"content-type": "application/x-www-form-urlencoded"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return requests.post(url=endpoint, auth=auth, data=data, headers=headers, timeout=30)

    def put_request(self, endpoint: str, data: dict) -> requests.Response:
        return requests.put(
            url=endpoint,
            auth=(self.secret_api_key, ""),
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

    def create_token(
        self, payway_obj: BankAccount | PayWayCard, payment_method: str, idempotency_key: str | None = None
    ) -> tuple[TokenResponse, list]:
        """
        Creates a single use token for a Customer's payment setup (credit card or bank account)
        :param payway_obj:   object: one of model.PayWayCard or model.BankAccount object
        :param payment_method:   str: one of `card` or `direct_debit`
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        data = payway_obj.to_dict()
        if payment_method == "card":
            payway_payment_method = CREDIT_CARD_PAYMENT_CHOICE
        elif payment_method == "direct_debit":
            payway_payment_method = BANK_ACCOUNT_PAYMENT_CHOICE
        else:
            valid_payment_method_choices = ", ".join(VALID_PAYMENT_METHOD_CHOICES)
            raise PaywayError(
                message=f"Invalid payment method. Must be one of {valid_payment_method_choices}",
                code="INVALID_PAYMENT_METHOD",
            )
        data.update(
            {
                "paymentMethod": payway_payment_method,
            },
        )
        endpoint = TOKEN_NO_REDIRECT
        logger.info("Sending Create Token request to PayWay.")
        response = self.post_request(
            endpoint,
            data,
            auth=(self.publishable_api_key, ""),
            idempotency_key=idempotency_key,
        )
        errors = self._validate_response(response)
        if errors:
            return None, errors
        token_response = TokenResponse().from_dict(response.json())
        return token_response, errors

    def create_card_token(self, card: PayWayCard, idempotency_key: str | None = None) -> tuple[TokenResponse, list]:
        """
        :param card:    PayWayCard object represents a customer's credit card details
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        return self.create_token(card, "card", idempotency_key=idempotency_key)

    def create_bank_account_token(self, bank_account: BankAccount, idempotency_key: str | None = None) -> str:
        """
        :param bank_account:    BankAccount object represents a customer's bank account
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        See model.BankAccount
        """
        return self.create_token(
            bank_account,
            "direct_debit",
            idempotency_key=idempotency_key,
        )

    def create_customer(self, customer: PayWayCustomer, idempotency_key: str | None = None) -> tuple[PayWayCustomer | None, list]:
        """
        Create a customer in PayWay system

        POST /customers to have PayWay generate the customer number
        PUT /customers/{customerNumber} to use your own customer number

        :param customer:    PayWayCustomer object represents a customer in PayWay
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        See model.PayWayCustomer
        :return:
        """

        data = customer.to_dict()
        data.update(
            {"merchantId": self.merchant_id, "bankAccountId": self.bank_account_id},
        )

        logger.info("Sending Create Customer request to PayWay.")

        if customer.custom_id:
            endpoint = f"{CUSTOMER_URL}/{customer.custom_id}"
            response = self.put_request(endpoint, data)
        else:
            endpoint = f"{CUSTOMER_URL}"
            response = self.post_request(
                endpoint,
                data,
                idempotency_key=idempotency_key,
            )

        errors = self._validate_response(response)
        if errors:
            return None, errors

        customer = PayWayCustomer().from_dict(response.json())
        return customer, errors

    def process_payment(self, payment: PayWayPayment, idempotency_key: str | None = None) -> tuple[PayWayTransaction, list]:
        """
        Process an individual payment against a Customer with active Recurring Billing setup.
        :param payment: PayWayPayment object (see model.PayWayPayment)
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        data = payment.to_dict()
        endpoint = TRANSACTION_URL
        logger.info("Sending Process Payment request to PayWay.")
        response = self.post_request(endpoint, data, idempotency_key=idempotency_key)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        # convert response to PayWayTransaction object
        transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def _validate_response(self, response: requests.Response) -> list | None:
        """
        Validates all responses from PayWay to catch documented PayWay errors.
        :param response: requests response object
        """
        if response.status_code in [
            400,
            401,
            403,
            405,
            406,
            407,
            409,
            410,
            415,
            429,
            501,
            503,
        ]:
            http_error_msg = f"{response.status_code} Client Error: {response.reason} for url: {response.url}"
            raise PaywayError(code=response.status_code, message=http_error_msg)

        if response.status_code in [404, 422]:  # Documented PayWay errors in JSON
            # parse error message
            return PaymentError().from_dict(response.json())

        if response.status_code == 500:
            try:
                errors = response.json()
            except json.JSONDecodeError:
                raise PaywayError(
                    code=response.status_code,
                    message="Internal server error",
                )
            # Documented PayWay server errors in JSON
            payway_error = ServerError().from_dict(errors)
            message = payway_error.to_message()
            raise PaywayError(code=response.status_code, message=message)

        return None

    def get_transaction(self, transaction_id: int) -> tuple[PayWayTransaction, list]:
        """
        Lookup and return a transaction if found in PayWay
        :param transaction_id: str  A PayWay transaction ID
        """
        endpoint = f"{TRANSACTION_URL}/{transaction_id}"
        response = self.get_request(endpoint)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def void_transaction(self, transaction_id: int, idempotency_key: str | None = None) -> tuple[PayWayTransaction, list]:
        """
        Void a transaction in PayWay
        :param transaction_id: str  A PayWay transaction ID
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        endpoint = f"{TRANSACTION_URL}/{transaction_id}/void"
        response = self.post_request(endpoint, data={}, idempotency_key=idempotency_key)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def refund_transaction(
        self,
        transaction_id: int,
        amount: float,
        order_id: str | None = None,
        ip_address: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[PayWayTransaction, list]:
        """
        Refund a transaction in PayWay
        :param transaction_id: str  A PayWay transaction ID
        :param amount:  str  amount to refund
        :param order_id:  str  optional reference number
        :param ip_address:  str  optional IP address
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        data = {
            "transactionType": "refund",
            "parentTransactionId": transaction_id,
            "principalAmount": amount,
        }
        if order_id:
            data["orderNumber"] = order_id
        if ip_address:
            data["customerIpAddress"] = ip_address
        response = self.post_request(TRANSACTION_URL, data, idempotency_key=idempotency_key)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def get_customer(self, customer_id: str) -> tuple[PayWayCustomer, list]:
        """
        Returns a PayWay Customer's Payment Setup, [Payment] Schedule, Contact Details, Custom Fields and Notes
        :param customer_id  str PayWay customer ID in PayWay system
        """
        endpoint = f"{CUSTOMER_URL}/{customer_id}"
        response = self.get_request(endpoint)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        customer = PayWayCustomer.from_dict(response.json())
        return customer, errors

    def update_payment_setup(self, token: str, customer_id: str) -> tuple[PaymentSetup, str]:
        """
        Updates the Customer's Payment Setup with a new Credit Card or Bank Account.
        :param token: PayWay credit card or bank account token
        :param customer_id: PayWay customer ID
        """
        endpoint = f"{CUSTOMER_URL}/{customer_id}/payment-setup"
        data = {
            "singleUseTokenId": token,
            "merchantId": self.merchant_id,
            "bankAccountId": self.bank_account_id,
        }
        response = self.put_request(endpoint, data)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        ps = PaymentSetup.from_dict(response.json())
        return ps, errors
