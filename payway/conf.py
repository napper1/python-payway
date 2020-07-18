import os

PAYWAY_API_URL = 'https://api.payway.com.au/rest/v1'
TOKEN_URL = PAYWAY_API_URL + '/single-use-tokens-redirect'
TRANSACTION_URL = PAYWAY_API_URL + '/transactions'
CUSTOMER_URL = PAYWAY_API_URL + '/customers'
OWN_BANK_ACCOUNTS_URL = PAYWAY_API_URL + '/your-bank-accounts'
TOKEN_NO_REDIRECT = PAYWAY_API_URL + '/single-use-tokens'

PUBLISHABLE_API_KEY = os.getenv('PAYWAY_PUBLISHABLE_API_KEY')
SECRET_API_KEY = os.getenv('PAYWAY_SECRET_API_KEY')
