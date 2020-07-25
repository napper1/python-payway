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
from payway.model import Card, Customer, Payment, Transaction, PaymentError


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
        cls.card = Card(
            card_number='4564710000000004',
            cvn='847',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='29'
        )
        cls.expired_card = Card(
            card_number='4564710000000012',
            cvn='963',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='15'
        )
        cls.stolen_card = Card(
            card_number='5163200000000016',
            cvn='728',
            card_holder_name='Test',
            expiry_date_month='12',
            expiry_date_year='29'
        )
        cls.declined_card = Card(
            card_number='4444333322221111',
            cvn='111',
            card_holder_name='Test',
            expiry_date_month='01',
            expiry_date_year='40'
        )
        cls.payment = Payment(
            customer_number='',
            transaction_type='payment',
            amount='10',
            currency='aud',
            order_number='5100',
            ip_address='127.0.0.1',
        )

    def test_create_token(self):
        card = self.card
        token, errors = self.client.create_token(card)

        self.assertIsNotNone(token)

    def test_create_customer(self):
        card = self.card
        token, errors = self.client.create_token(card)
        customer = self.customer
        customer.token = token
        payway_customer_number, customer_errors = self.client.create_customer(customer)

        self.assertIsNotNone(payway_customer_number)

    def test_process_payment(self):
        card = self.card
        token, errors = self.client.create_token(card)
        customer = self.customer
        customer.token = token
        payway_customer_number, customer_errors = self.client.create_customer(customer)
        payment = self.payment
        payment.customer_number = payway_customer_number
        payment.order_number = '5100'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsInstance(transaction, Transaction)
        self.assertIsNone(errors)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertIsNotNone(transaction.receipt_number)
        self.assertEqual(transaction.status, "approved")
        self.assertEqual(transaction.response_code, "08")

    def test_expiry_date(self):
        card = self.expired_card
        token, errors = self.client.create_token(card)

        self.assertIsNone(token)
        self.assertIsNotNone(errors)
        self.assertIsInstance(errors, list)
        payway_error = errors[0]
        self.assertIsInstance(payway_error, PaymentError)
        self.assertEqual(payway_error.field_name, 'expiryDateMonth')

    def test_expired_card(self):
        card = copy.deepcopy(self.expired_card)
        card.expiry_date_year = '30'
        token, errors = self.client.create_token(card)
        self.assertIsNotNone(token)
        customer = self.customer
        customer.token = token
        payway_customer_number, customer_errors = self.client.create_customer(customer)
        payment = self.payment
        payment.customer_number = payway_customer_number
        payment.order_number = '5101'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, Transaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '54')
        self.assertEqual(transaction.response_text, 'Expired card')

    def test_stolen_card(self):
        card = self.stolen_card
        token, errors = self.client.create_token(card)
        self.customer.token = token
        payway_customer_number, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer_number
        payment.order_number = '5102'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, Transaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '04')
        self.assertEqual(transaction.response_text, 'Pick-up card')

    def test_declined_card(self):
        card = self.declined_card
        token, errors = self.client.create_token(card)
        self.customer.token = token
        payway_customer_number, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer_number
        payment.order_number = '5103'

        transaction, errors = self.client.process_payment(payment)
        self.assertIsNone(errors)
        self.assertIsInstance(transaction, Transaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '42')
        self.assertEqual(transaction.response_text, 'No universal account')
