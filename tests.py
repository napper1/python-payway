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
from payway.model import Card, Customer, Payment, Transaction


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # You will need to create a sandbox PayWay account and add your sandbox API keys into your environment
        merchant_id = 'TEST'
        bank_account_id = '0000000A'
        publishable_api_key = PUBLISHABLE_API_KEY
        secret_api_key = SECRET_API_KEY
        redirect_url = 'http://localhost'

        cls.client = Client(merchant_id=merchant_id,
                            bank_account_id=bank_account_id,
                            publishable_api_key=publishable_api_key,
                            secret_api_key=secret_api_key,
                            redirect_url=redirect_url)

        cls.card = Card(
            card_number='4564710000000004',
            cvn='847',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='29'
        )
        cls.customer = Customer(
            custom_id='c981a',
            customer_name='John Smith',
            email_address='johnsmith@example.com',
            send_email_receipts=False,  # not available in sandbox
            phone_number='0343232323',
            street='1 Test Street',
            street2='2 Test Street',
            city_name='Sydney',
            state='NSW',
            postal_code='2000',
        )

    def test_create_token(self):
        card = self.card
        token = self.client.create_token(card)

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    def test_create_customer(self):
        card = self.card
        token = self.client.create_token(card)
        customer = self.customer
        customer.token = token
        payway_customer_number = self.client.create_customer(customer)

        self.assertIsNotNone(payway_customer_number)
        self.assertIsInstance(payway_customer_number, str)

    def test_process_payment(self):
        card = self.card
        token = self.client.create_token(card)
        customer = self.customer
        customer.token = token
        payway_customer_number = self.client.create_customer(customer)

        payment = Payment(
            customer_number=payway_customer_number,
            transaction_type='payment',
            amount='10',
            currency='aud',
            order_number='5100',
            ip_address='127.0.0.1',
        )
        transaction = self.client.process_payment(payment)

        self.assertIsInstance(transaction, Transaction)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertIsNotNone(transaction.receipt_number)
        self.assertEqual(transaction.status, "approved")
        self.assertEqual(transaction.response_code, "08")
