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


class TestCustomerRequest(unittest.TestCase):

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

    def test_stop_and_start_all_payments(self):
        # create customer with a stored card
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        # stop payments for customer
        stop_payment_resp = self.client.stop_all_payments(payway_customer_number)
        self.assertEqual(stop_payment_resp.__class__, dict)
        stopped = stop_payment_resp.get("stopped")
        self.assertEqual(stopped, True)
        # now test start method
        start_payment_resp = self.client.start_all_payments(payway_customer_number)
        self.assertEqual(start_payment_resp.__class__, dict)
        stopped = start_payment_resp.get("stopped")
        self.assertEqual(stopped, False)

    def test_delete_customer(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = copy.deepcopy(self.customer)
        # testing with a brand new customer - customers with existing payments in the past 365 days cannot be deleted
        customer.custom_id = ''
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        # stop customer payments to allow deletion
        stop_payment_resp = self.client.stop_all_payments(payway_customer_number)
        stopped = stop_payment_resp.get("stopped")
        self.assertEqual(stopped, True)
        # delete customer record in PayWay
        response = self.client.delete_customer(payway_customer_number)
        self.assertEqual(response.status_code, 204)

    def test_schedule_payments(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        response = self.client.schedule_payments(payway_customer_number, 'weekly', '01 Sep 2020', 10.50)
        self.assertEqual(response.__class__, dict)
        self.assertEqual(response['frequency'], 'weekly')
        self.assertEqual(response['nextPaymentDate'], '01 Sep 2020')
        self.assertEqual(response['nextPrincipalAmount'], 10.50)
        self.assertEqual(response['regularPrincipalAmount'], 10.50)
        self.assertEqual(response['regularPaymentAmount'], 10.50)

    def test_stop_schedule(self):
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        response = self.client.schedule_payments(payway_customer_number, 'weekly', '01 Sep 2020', 10.50)
        self.assertEqual(response.__class__, dict)
        self.assertEqual(response['frequency'], 'weekly')
        # stop schedule
        response = self.client.stop_schedule(payway_customer_number)
        self.assertEqual(response.status_code, 204)

    def test_update_contact_details(self):
        new_name = 'Jack Smith'
        new_email = 'jacksmith@example.com'
        new_phone = '0353532323'
        new_street1 = '3 Test St'
        new_street2 = 'Apt 1'
        new_city = 'Melbourne'
        new_state = 'VIC'
        new_postcode = '3029'
        update_details = {
            'customerName': new_name,
            'emailAddress': new_email,
            'phoneNumber': new_phone,
            'street1': new_street1,
            'street2': new_street2,
            'cityName': new_city,
            'state': new_state,
            'postalCode': new_postcode,
        }
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        # update contact details
        response = self.client.update_contact_details(payway_customer.customer_number, **update_details)
        self.assertEqual(response['customerName'], new_name)
        self.assertEqual(response['emailAddress'], new_email)
        self.assertEqual(response['phoneNumber'], new_phone)
        address = response['address']
        self.assertEqual(address['street1'], new_street1)
        self.assertEqual(address['street2'], new_street2)
        self.assertEqual(address['cityName'], new_city)
        self.assertEqual(address['state'], new_state)
        self.assertEqual(address['postalCode'], new_postcode)

    def test_list_customers(self):
        # create a customer if none already and list all customers
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        response = self.client.list_customers()
        self.assertEqual(response.__class__, dict)
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.get('data'))
