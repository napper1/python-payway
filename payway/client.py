from logging import getLogger
import requests

from payway.conf import TOKEN_NO_REDIRECT, CUSTOMER_URL, TRANSACTION_URL
from payway.constants import CREDIT_CARD_PAYMENT_CHOICE
from payway.exception import PaywayError
from payway.model import Customer, Transaction, PaymentError, ServerError


logger = getLogger(__name__)


class Client(object):
    """
    Abstract client implementation.
    Contains credentials, logger and an endpoint instance.
    """

    merchant_id = ''
    bank_account_id = ''
    secret_api_key = ''
    publishable_api_key = ''
    redirect_url = ''

    def __init__(self, merchant_id, bank_account_id, secret_api_key, publishable_api_key, redirect_url=None):
        """
        :param merchant_id        : str                 = PayWay Merchant ID
        :param bank_account_id   : str                  = PayWay Bank Account ID
        :param secret_api_key   : str                   = PayWay Secret APi Key
        :param publishable_api_key   : str              = PayWay Publishable API Key
        :param redirect_url   : str                     = PayWay Redirect URL
        """

        self._validate_credentials(merchant_id, bank_account_id, secret_api_key, publishable_api_key, redirect_url)
        self.merchant_id = merchant_id
        self.bank_account_id = bank_account_id
        self.secret_api_key = secret_api_key
        self.publishable_api_key = publishable_api_key
        self.redirect_url = redirect_url

    def _validate_credentials(self, merchant_id, bank_account_id, secret_api_key, publishable_api_key, redirect_url):
        if not merchant_id or not bank_account_id or not secret_api_key or not publishable_api_key:
            if not secret_api_key or not publishable_api_key:
                logger.error('PayWay API keys not found')
                raise PaywayError(message='PayWay API keys not found', code="INVALID_API_KEYS")
            logger.error('Merchant ID, bank account ID, secret API key, publishable API key are '
                         'invalid')
            raise PaywayError(message='Invalid credentials', code='INVALID_API_CREDENTIALS')

    def create_token(self, card):
        """
        Creates a single use token for a Customer's payment setup (credit card or bank account)
        by POSTing to PayWay and reading the token from the redirect response URL.
        Takes a valid form.
        N.B. Creating a token doesn't mean the payment setup details are correct.
        """
        data = card.to_dict()
        data.update({
            'paymentMethod': CREDIT_CARD_PAYMENT_CHOICE,
        })
        endpoint = TOKEN_NO_REDIRECT
        logger.info('Sending Create Token request to PayWay.')
        response = requests.post(url=endpoint, auth=(self.publishable_api_key, ''), data=data)
        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            new_token_id = response.json().get("singleUseTokenId")
            # todo: could return full response which has credit card (masked) too along with token id
            return new_token_id, errors

    def create_customer(self, customer):
        # use kwargs?
        data = customer.to_dict()
        data.update({
            "merchantId": self.merchant_id,
            "bankAccountId": self.bank_account_id
        })
        # POST /customers to have PayWay generate the customer number
        # PUT /customers/{customerNumber} to use your own customer number

        logger.info('Sending Create Customer request to PayWay.')

        if customer.custom_id:
            endpoint = '{}/{}'.format(CUSTOMER_URL, customer.custom_id)
            response = requests.put(url=endpoint, auth=(self.secret_api_key, ''), data=data)
        else:
            endpoint = '{}/{}'.format(CUSTOMER_URL, customer.id) % (CUSTOMER_URL, str(customer.bc_entity_id))
            response = requests.post(url=endpoint, auth=(self.secret_api_key, ''), data=data)

        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            customer_number = response.json()['customerNumber']
            # todo: could return a Customer object with the updated payway customer number in it
            return customer_number, errors

    def process_payment(self, payment):
        """
        Process an individual payment against a Customer with active Recurring Billing setup.
        Amount is dollars and cents, i.e. 10.50, 0.50
        """
        data = payment.to_dict()
        endpoint = TRANSACTION_URL
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        logger.info('Sending Process Payment request to PayWay.')
        response = requests.post(url=endpoint, auth=(self.secret_api_key, ''), data=data, headers=headers)
        logger.info('Response from server: %s' % response)
        errors = self._validate_response(response)
        if errors:
            return None, errors
        else:
            # convert response to Transaction object
            transaction = Transaction.from_json(response.json())
        return transaction, errors

    def _validate_response(self, response):

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
