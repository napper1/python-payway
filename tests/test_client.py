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


class TestClient(unittest.TestCase):

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
        cls.stolen_card = PayWayCard(
            card_number='5163200000000016',
            cvn='728',
            card_holder_name='Test',
            expiry_date_month='12',
            expiry_date_year='29'
        )
        cls.declined_card = PayWayCard(
            card_number='4444333322221111',
            cvn='111',
            card_holder_name='Test',
            expiry_date_month='01',
            expiry_date_year='40'
        )
        cls.payment = PayWayPayment(
            customer_number='',
            transaction_type='payment',
            amount='10',
            currency='aud',
            order_number='5100',
            ip_address='127.0.0.1',
        )
        cls.pre_auth_payment = PayWayPayment(
            customer_number='',
            transaction_type='preAuth',
            amount='2.15',
            currency='aud',
            order_number='5110',
            ip_address='127.0.0.1',
        )
        cls.pre_auth_capture_payment = PayWayPayment(
            transaction_type='capture',
            parent_transaction_id='',
            amount='2.15',
            order_number='5111',
            ip_address='127.0.0.1',
        )
        cls.bank_account = BankAccount(
            account_name='Test',
            bsb='000-000',
            account_number=123456,
        )
        cls.invalid_bank_account = BankAccount(
            account_name='Test',
            bsb='000-001',
            account_number=123456,
        )

    def test_create_token(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)

        self.assertIsNotNone(token_response.token)

    def test_create_customer(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)

    def test_create_customer_without_id(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = copy.deepcopy(self.customer)
        customer.custom_id = ""
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)

    def test_process_payment(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5100'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertIsNone(errors)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertIsNotNone(transaction.receipt_number)
        self.assertEqual(transaction.status, "approved")
        self.assertEqual(transaction.response_code, "08")

    def test_expiry_date(self):
        card = self.expired_card
        token_response, errors = self.client.create_card_token(card)

        self.assertIsNone(token_response)
        self.assertIsNotNone(errors)
        self.assertIsInstance(errors, list)
        payway_error = errors[0]
        self.assertIsInstance(payway_error, PaymentError)
        self.assertEqual(payway_error.field_name, 'expiryDateMonth')

    def test_expired_card(self):
        card = copy.deepcopy(self.expired_card)
        card.expiry_date_year = '30'
        token_response, errors = self.client.create_card_token(card)
        self.assertIsNotNone(token_response.token)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5101'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '54')
        self.assertEqual(transaction.response_text, 'Expired card')

    def test_stolen_card(self):
        card = self.stolen_card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5102'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '04')
        self.assertEqual(transaction.response_text, 'Pick-up card')

    def test_declined_card(self):
        card = self.declined_card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5103'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertEqual(transaction.status, 'declined')
        self.assertEqual(transaction.response_code, '42')
        self.assertEqual(transaction.response_text, 'No universal account')

    def test_direct_debit_payment(self):
        bank_account = self.bank_account
        token_response, errors = self.client.create_bank_account_token(bank_account)
        token = token_response.token
        self.assertIsNotNone(token)
        self.customer.token = token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5104'
        transaction, errors = self.client.process_payment(payment)

        self.assertIsNone(errors)
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertEqual(transaction.status, 'approved*')
        self.assertEqual(transaction.response_code, 'G')
        # PayWay direct debit payments need to be polled in the future to determine transaction outcome

    def test_invalid_direct_debit(self):
        bank_account = self.invalid_bank_account
        token_response, errors = self.client.create_bank_account_token(bank_account)
        self.assertIsNotNone(errors)
        payway_error = errors[0]
        self.assertEqual(payway_error.message, 'Invalid BSB.')

    def test_get_transaction_card(self):
        # create a transaction using valid card
        # then poll PayWay for transaction details
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5105'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)
        polled_transaction, poll_errors = self.client.get_transaction(transaction.transaction_id)
        self.assertIsNotNone(polled_transaction)
        self.assertIsNotNone(polled_transaction.transaction_id)
        self.assertEqual(polled_transaction.transaction_id, transaction.transaction_id)

    def test_get_transaction_direct_debit(self):
        # create a transaction using direct debit
        # then poll PayWay for updated transaction
        bank_account = self.bank_account
        token_response, errors = self.client.create_bank_account_token(bank_account)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5106'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)
        polled_transaction, poll_errors = self.client.get_transaction(transaction.transaction_id)
        self.assertIsNotNone(polled_transaction)
        self.assertIsNotNone(polled_transaction.transaction_id)
        self.assertEqual(polled_transaction.transaction_id, transaction.transaction_id)

    def test_void(self):
        # void a transaction in PayWay
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5105'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)
        void_transaction, void_errors = self.client.void_transaction(transaction.transaction_id)
        self.assertIsNone(errors)
        self.assertIsNotNone(void_transaction)
        self.assertEqual(void_transaction.status, 'voided')

    def test_refund(self):
        # create a transaction then refund in PayWay
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5106'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)

        refund, refund_errors = self.client.refund_transaction(
            transaction_id=transaction.transaction_id,
            amount=transaction.principal_amount,
        )
        # Payment is only refundable after it settles and so this test should produce an error from PayWay
        self.assertIsNotNone(refund_errors)
        payway_error = refund_errors[0]
        self.assertEqual(
            payway_error.message,
            'Credit card payments are only refundable after they have settled. You must void this payment instead.'
        )

    def test_get_customer(self):
        # get all customer details from PayWay
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)

        customer, customer_errors = self.client.get_customer(payway_customer.customer_number)
        self.assertIsNotNone(customer)
        self.assertIsNone(customer_errors)
        self.assertEqual(customer.customer_number, payway_customer.customer_number)

    def test_update_payment_setup_card(self):
        # update card or bank account in PayWay from token
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        # update customer with another card
        card_token_response, card_errors = self.client.create_card_token(self.declined_card)
        ps, ps_errors = self.client.update_payment_setup(card_token_response.token, payway_customer.customer_number)
        self.assertIsNone(ps_errors)
        self.assertIsNotNone(ps)

    def test_pre_auth_payment(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)
        payment = self.pre_auth_payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5110'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)

    def test_pre_auth_capture(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        self.customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(self.customer)

        # first create a pre auth transaction to be later charged from the stored card
        payment = self.pre_auth_payment
        payment.customer_number = payway_customer.customer_number
        payment.order_number = '5111'
        transaction, errors = self.client.process_payment(payment)
        self.assertIsNotNone(transaction)

        # then capture the pre auth transaction in a new payment
        capture_payment = self.pre_auth_capture_payment
        capture_payment.parent_transaction_id = transaction.transaction_id
        capture_payment.order_number = '5112'
        capture_transaction, capture_errors = self.client.process_payment(capture_payment)

        self.assertIsNotNone(capture_transaction)
        self.assertIsNotNone(capture_transaction.transaction_id)


