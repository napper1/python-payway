from __future__ import annotations

import json
import time
from collections.abc import Callable
from http import HTTPStatus
from logging import getLogger
from typing import Any

import requests

from payway.constants import (
    BANK_ACCOUNT_PAYMENT_CHOICE,
    CREDIT_CARD_PAYMENT_CHOICE,
    CUSTOMER_URL,
    PAYWAY_ERROR_RESPONSE_CODES,
    RETRYABLE_STATUS_CODES,
    TOKEN_NO_REDIRECT,
    TRANSACTION_URL,
    VALID_PAYMENT_METHOD_CHOICES,
    PaymentMethod,
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

    def __init__(  # noqa: PLR0913
        self,
        merchant_id: str,
        bank_account_id: str,
        secret_api_key: str,
        publishable_api_key: str,
        *,
        max_retries: int = 0,
        retry_delay: float = 1.0,
    ) -> None:
        """
        :param merchant_id: PayWay Merchant ID
        :param bank_account_id: PayWay Bank Account ID
        :param secret_api_key: PayWay Secret APi Key
        :param publishable_api_key: PayWay Publishable API Key
        :param max_retries: retries per request on network errors and HTTP 429/503 (0 disables)
        :param retry_delay: base seconds to wait between attempts (Retry-After header wins if present)
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
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        session = requests.Session()
        session.auth = (self.secret_api_key, "")
        session.headers["content-type"] = "application/x-www-form-urlencoded"
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
    ) -> None:
        if any(not key for key in (secret_api_key, publishable_api_key)):
            logger.error("PayWay API keys not found")
            raise PaywayError(
                message="PayWay API keys not found",
                code="INVALID_API_KEYS",
            )
        if any(not val for val in (merchant_id, bank_account_id)):
            logger.error("Merchant ID or bank account ID invalid")
            raise PaywayError(
                message="Invalid credentials",
                code="INVALID_API_CREDENTIALS",
            )

    def get_request(self, endpoint: str) -> requests.Response:
        return self._send_with_retries(
            lambda: requests.get(url=endpoint, auth=(self.secret_api_key, ""), timeout=30),
            can_retry=True,
        )

    def post_request(
        self, endpoint: str, data: dict[str, Any], auth: tuple[str, str] | None = None, idempotency_key: str | None = None
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
        return self._send_with_retries(
            lambda: requests.post(url=endpoint, auth=auth, data=data, headers=headers, timeout=30),
            can_retry=bool(idempotency_key),
        )

    def _send_with_retries(self, send: Callable[[], requests.Response], *, can_retry: bool) -> requests.Response:
        """
        Resend on network errors and HTTP 429/503 per PayWay's retry guidance
        https://www.payway.com.au/docs/rest.html#network-errors
        Requests without an Idempotency-Key must pass can_retry=False: retrying
        them could double-charge. Other statuses (including 500/502/504) are
        returned as-is.
        """
        retries = self.max_retries if can_retry else 0
        for attempt in range(retries):
            try:
                response = send()
            except (requests.ConnectionError, requests.Timeout) as exc:
                logger.warning("PayWay request failed (%s), retrying", exc)
                time.sleep(self._retry_wait(attempt, None))
                continue
            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response
            logger.warning("PayWay responded %s, retrying", response.status_code)
            time.sleep(self._retry_wait(attempt, response))
        return send()

    def _retry_wait(self, attempt: int, response: requests.Response | None) -> float:
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        return self.retry_delay * (attempt + 1)

    def put_request(self, endpoint: str, data: dict[str, Any]) -> requests.Response:
        # No Idempotency-Key is sent on PUTs, so they are never retried
        return requests.put(
            url=endpoint,
            auth=(self.secret_api_key, ""),
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

    def create_token(
        self, payway_obj: BankAccount | PayWayCard, payment_method: PaymentMethod | str, idempotency_key: str | None = None
    ) -> tuple[TokenResponse | None, list[PaymentError] | None]:
        """
        Creates a single use token for a Customer's payment setup (credit card or bank account)
        :param payway_obj:   object: one of model.PayWayCard or model.BankAccount object
        :param payment_method:   PaymentMethod or str: one of `card` or `direct_debit`
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        try:
            payment_method = PaymentMethod(payment_method)
        except ValueError as exc:
            valid_payment_method_choices = ", ".join(VALID_PAYMENT_METHOD_CHOICES)
            raise PaywayError(
                message=f"Invalid payment method. Must be one of {valid_payment_method_choices}",
                code="INVALID_PAYMENT_METHOD",
            ) from exc
        data = payway_obj.to_dict()
        if payment_method is PaymentMethod.CARD:
            data["paymentMethod"] = CREDIT_CARD_PAYMENT_CHOICE
        else:
            data["paymentMethod"] = BANK_ACCOUNT_PAYMENT_CHOICE
        logger.info("Sending Create Token request to PayWay.")
        response = self.post_request(
            TOKEN_NO_REDIRECT,
            data,
            auth=(self.publishable_api_key, ""),
            idempotency_key=idempotency_key,
        )
        errors = self._validate_response(response)
        if errors:
            return None, errors
        return TokenResponse.from_dict(response.json()), errors

    def create_card_token(
        self, card: PayWayCard, idempotency_key: str | None = None
    ) -> tuple[TokenResponse | None, list[PaymentError] | None]:
        """
        :param card:    PayWayCard object represents a customer's credit card details
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        """
        return self.create_token(card, PaymentMethod.CARD, idempotency_key=idempotency_key)

    def create_bank_account_token(
        self, bank_account: BankAccount, idempotency_key: str | None = None
    ) -> tuple[TokenResponse | None, list[PaymentError] | None]:
        """
        :param bank_account:    BankAccount object represents a customer's bank account
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        See model.BankAccount
        """
        return self.create_token(
            bank_account,
            PaymentMethod.DIRECT_DEBIT,
            idempotency_key=idempotency_key,
        )

    def create_customer(
        self, customer: PayWayCustomer, idempotency_key: str | None = None
    ) -> tuple[PayWayCustomer | None, list[PaymentError] | None]:
        """
        Create a customer in PayWay system
        POST /customers to have PayWay generate the customer number
        PUT /customers/{customerNumber} to use your own customer number
        :param customer:    PayWayCustomer object represents a customer in PayWay
        :param idempotency_key:   str: unique value to avoid duplicate POSTs
        See model.PayWayCustomer
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
        customer = PayWayCustomer.from_dict(response.json())
        return customer, errors

    def process_payment(
        self, payment: PayWayPayment, idempotency_key: str | None = None
    ) -> tuple[PayWayTransaction | None, list[PaymentError] | None]:
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

    def _validate_response(self, response: requests.Response) -> list[PaymentError] | None:
        """
        Validates all responses from PayWay to catch documented PayWay errors.
        :param response: requests response object
        """
        if response.status_code in PAYWAY_ERROR_RESPONSE_CODES:
            http_error_msg = f"{response.status_code} Client Error: {response.reason} for url: {response.url}"
            raise PaywayError(code=str(response.status_code), message=http_error_msg)

        if response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY]:  # Documented PayWay errors in JSON
            return PaymentError.from_dict(response.json())

        if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            try:
                errors = response.json()
            except json.JSONDecodeError as exc:
                raise PaywayError(
                    code=str(response.status_code),
                    message="Internal server error",
                ) from exc
            # Documented PayWay server errors in JSON
            payway_error = ServerError.from_dict(errors)
            message = payway_error.to_message()
            raise PaywayError(code=str(response.status_code), message=message)

        return None

    def get_transaction(self, transaction_id: int) -> tuple[PayWayTransaction | None, list[PaymentError] | None]:
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

    def void_transaction(
        self, transaction_id: int, idempotency_key: str | None = None
    ) -> tuple[PayWayTransaction | None, list[PaymentError] | None]:
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
        return PayWayTransaction.from_dict(response.json()), errors

    def refund_transaction(
        self,
        transaction_id: int,
        amount: float,
        order_id: str | None = None,
        ip_address: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[PayWayTransaction | None, list[PaymentError] | None]:
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
        return PayWayTransaction.from_dict(response.json()), errors

    def get_customer(self, customer_id: str) -> tuple[PayWayCustomer | None, list[PaymentError] | None]:
        """
        Returns a PayWay Customer's Payment Setup, [Payment] Schedule, Contact Details, Custom Fields and Notes
        :param customer_id  str PayWay customer ID in PayWay system
        """
        endpoint = f"{CUSTOMER_URL}/{customer_id}"
        response = self.get_request(endpoint)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        return PayWayCustomer.from_dict(response.json()), errors

    def update_payment_setup(self, token: str, customer_id: str) -> tuple[PaymentSetup | None, list[PaymentError] | None]:
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
        return PaymentSetup.from_dict(response.json()), errors
