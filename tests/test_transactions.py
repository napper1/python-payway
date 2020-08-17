import copy
import os
import unittest

try:
    import payway
except:
    from os.path import dirname, join
    from sys import path
    path.append(join(dirname(__file__), '..'))


from payway.client import Client
from payway.conf import PUBLISHABLE_API_KEY, SECRET_API_KEY
from payway.model import PayWayCard, PayWayCustomer, PayWayPayment, PayWayTransaction, PaymentError, BankAccount


class TestTransactionRequest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # You will need to create a sandbox PayWay account and add your sandbox API keys into your environment
        merchant_id = 'TEST'
        bank_account_id = '0000000A'
        publishable_api_key = PUBLISHABLE_API_KEY
        secret_api_key = SECRET_API_KEY

        cls.client = Client(merchant_id=merchant_id,
                            bank_account_id=bank_account_id,
                            publishable_api_key=publishable_api_key,
                            secret_api_key=secret_api_key,
                            )
        cls.customer = PayWayCustomer(
            custom_id='c981b',
            customer_name='Jane Smith',
            email_address='janesmith@example.com',
            send_email_receipts=False,  # not available in sandbox
            phone_number='0343232323',
            street='1 Test Street',
            street2='2 Test Street',
            city_name='Sydney',
            state='NSW',
            postal_code='2000',
        )
        cls.card = PayWayCard(
            card_number='4564710000000004',
            cvn='847',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='29'
        )
        cls.expired_card = PayWayCard(
            card_number='4564710000000012',
            cvn='963',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='15'
        )
        cls.payment = PayWayPayment(
            customer_number='',
            transaction_type='payment',
            amount='10',
            currency='aud',
            order_number='5100',
            ip_address='127.0.0.1',
        )

    def test_search_transactions(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        # create transaction
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5115'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertIsNone(errors)
        # search transaction
        query = '/search-customer?customerNumber=%s' % payway_customer_number
        response = self.client.search_transactions(query)
        self.assertEqual(response.__class__, dict)
        transactions = response['data']
        self.assertIsNotNone(transactions)
