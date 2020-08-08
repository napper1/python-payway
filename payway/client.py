from logging import getLogger
import requests

from payway.conf import TOKEN_NO_REDIRECT, CUSTOMER_URL, TRANSACTION_URL
from payway.constants import CREDIT_CARD_PAYMENT_CHOICE, BANK_ACCOUNT_PAYMENT_CHOICE, PAYMENT_METHOD_CHOICES, \
    VALID_PAYMENT_METHOD_CHOICES
from payway.exceptions import PaywayError
from payway.model import PayWayCustomer, PayWayTransaction, PaymentError, ServerError, PaymentSetup, TokenResponse

logger = getLogger(__name__)


class Client(object):
    """
    PayWay Client to connect to PayWay and perform methods given credentials
    """

    merchant_id = ''
    bank_account_id = ''
    secret_api_key = ''
    publishable_api_key = ''

    def __init__(self, merchant_id, bank_account_id, secret_api_key, publishable_api_key):
        """
        :param merchant_id        : str                 = PayWay Merchant ID
        :param bank_account_id   : str                  = PayWay Bank Account ID
        :param secret_api_key   : str                   = PayWay Secret APi Key
        :param publishable_api_key   : str              = PayWay Publishable API Key
        """
        self._validate_credentials(merchant_id, bank_account_id, secret_api_key, publishable_api_key)
        self.merchant_id = merchant_id
        self.bank_account_id = bank_account_id
        self.secret_api_key = secret_api_key
        self.publishable_api_key = publishable_api_key

    def _validate_credentials(self, merchant_id, bank_account_id, secret_api_key, publishable_api_key):
        if not merchant_id or not bank_account_id or not secret_api_key or not publishable_api_key:
            if not secret_api_key or not publishable_api_key:
                logger.error('PayWay API keys not found')
                raise PaywayError(message='PayWay API keys not found', code="INVALID_API_KEYS")
            logger.error('Merchant ID, bank account ID, secret API key, publishable API key are '
                         'invalid')
            raise PaywayError(message='Invalid credentials', code='INVALID_API_CREDENTIALS')

    def get_request(self, endpoint):
        return requests.get(url=endpoint, auth=(self.secret_api_key, ''))

    def post_request(self, endpoint, data, auth=None):
        if not auth:
            auth = (self.secret_api_key, '')
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        return requests.post(url=endpoint, auth=auth, data=data, headers=headers)

    def put_request(self, endpoint, data):
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        return requests.put(url=endpoint, auth=(self.secret_api_key, ''), data=data, headers=headers)

    def create_token(self, payway_obj, payment_method):
        """
        Creates a single use token for a Customer's payment setup (credit card or bank account)
        :param payway_obj:   object: one of model.PayWayCard or model.BankAccount object
        :param payment_method:   str: one of `card` or `direct_debit`
        """
        data = payway_obj.to_dict()
        if payment_method == 'card':
            payway_payment_method = CREDIT_CARD_PAYMENT_CHOICE
        elif payment_method == 'direct_debit':
            payway_payment_method = BANK_ACCOUNT_PAYMENT_CHOICE
        elif payment_method not in VALID_PAYMENT_METHOD_CHOICES:
            raise PaywayError(
                message="Invalid payment method. Must be one of %s" % ', '.join(VALID_PAYMENT_METHOD_CHOICES),
                code='INVALID_PAYMENT_METHOD')
        data.update({
            'paymentMethod': payway_payment_method,
        })
        endpoint = TOKEN_NO_REDIRECT
        logger.info('Sending Create Token request to PayWay.')
        response = self.post_request(endpoint, data, auth=(self.publishable_api_key, ''))
        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            token_response = TokenResponse().from_dict(response.json())
            return token_response, errors

    def create_card_token(self, card):
        """
        :param card:    PayWayCard object represents a customer's credit card details
        See model.PayWayCard
        """
        return self.create_token(card, 'card')

    def create_bank_account_token(self, bank_account):
        """
        :param bank_account:    BankAccount object represents a customer's bank account
        See model.BankAccount
        """
        return self.create_token(bank_account, 'direct_debit')

    def create_customer(self, customer):
        """
        Create a customer in PayWay system

        POST /customers to have PayWay generate the customer number
        PUT /customers/{customerNumber} to use your own customer number

        :param customer:    PayWayCustomer object represents a customer in PayWay
        See model.PayWayCustomer
        :return:
        """

        data = customer.to_dict()
        data.update({
            "merchantId": self.merchant_id,
            "bankAccountId": self.bank_account_id
        })

        logger.info('Sending Create Customer request to PayWay.')

        if customer.custom_id:
            endpoint = '{}/{}'.format(CUSTOMER_URL, customer.custom_id)
            response = self.put_request(endpoint, data)
        else:
            endpoint = '{}'.format(CUSTOMER_URL)
            response = self.post_request(endpoint, data)

        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            customer = PayWayCustomer().from_dict(response.json())
            return customer, errors

    def process_payment(self, payment):
        """
        Process an individual payment against a Customer with active Recurring Billing setup.
        :param payment: PayWayPayment object (see model.PayWayPayment)
        """
        data = payment.to_dict()
        endpoint = TRANSACTION_URL
        logger.info('Sending Process Payment request to PayWay.')
        response = self.post_request(endpoint, data)
        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            # convert response to PayWayTransaction object
            transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def _validate_response(self, response):
        """
        Validates all responses from PayWay to catch documented PayWay errors.
        :param response: requests response object
        """
        if response.status_code in [400, 401, 403, 405, 406, 407, 409, 410, 415, 429, 501, 503]:
            http_error_msg = '%s Client Error: %s for url: %s' % (response.status_code, response.reason, response.url)
            raise PaywayError(code=response.status_code, message=http_error_msg)

        elif response.status_code in [404, 422]:  # Documented PayWay errors in JSON
            # parse error message
            errors = response.json()
            payway_errors = PaymentError().from_dict(errors)
            # instead of raising an exception, return the specific PayWay errors as a list
            return payway_errors

        elif response.status_code == 500:  # Documented PayWay server errors in JSON
            errors = response.json()
            payway_error = ServerError().from_dict(errors)
            message = payway_error.to_message()
            raise PaywayError(code=response.status_code, message=message)

        else:
            return None

    def get_transaction(self, transaction_id):
        """
        Lookup and return a transaction if found in PayWay
        :param transaction_id: str  A PayWay transaction ID
        """
        endpoint = '%s/%s' % (TRANSACTION_URL, str(transaction_id))
        response = self.get_request(endpoint)
        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def void_transaction(self, transaction_id):
        """
        Void a transaction in PayWay
        :param transaction_id: str  A PayWay transaction ID
        """
        endpoint = '%s/%s/void' % (TRANSACTION_URL, transaction_id)
        response = self.post_request(endpoint, data={})
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            transaction = PayWayTransaction.from_dict(response.json())
        return transaction, errors

    def refund_transaction(self, transaction_id, amount, order_id=None, ip_address=None):
        """
        Refund a transaction in PayWay
        :param transaction_id: str  A PayWay transaction ID
        :param amount:  str  amount to refund
        :param order_id:  str  optional reference number
        :param ip_address:  str  optional IP address
        """
        endpoint = TRANSACTION_URL
        data = {
            'transactionType': 'refund',
            'parentTransactionId': transaction_id,
            'principalAmount': amount,
        }
        if order_id:
            data['orderNumber'] = order_id
        if ip_address:
            data['customerIpAddress'] = ip_address
        response = self.post_request(endpoint, data)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            transaction = PayWayTransaction.from_dict(response)
        return transaction, errors

    def get_customer(self, customer_id):
        """
        Returns a PayWay Customer's Payment Setup, [Payment] Schedule, Contact Details, Custom Fields and Notes
        :param customer_id  str PayWay customer ID in PayWay system
        """
        endpoint = '%s/%s' % (CUSTOMER_URL, str(customer_id))
        response = self.get_request(endpoint)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            customer = PayWayCustomer.from_dict(response.json())
        return customer, errors

    def update_payment_setup(self, token, customer_id):
        """
        Updates the Customer's Payment Setup with a new Credit Card or Bank Account.
        :param token: PayWay credit card or bank account token
        :param customer_id: PayWay customer ID
        """
        endpoint = '%s/%s/payment-setup' % (CUSTOMER_URL, str(customer_id))
        data = {
            "singleUseTokenId": token,
            "merchantId": self.merchant_id,
            "bankAccountId": self.bank_account_id
        }
        response = self.put_request(endpoint, data)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            ps = PaymentSetup.from_dict(response.json())
        return ps, errors
