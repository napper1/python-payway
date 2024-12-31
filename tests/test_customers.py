from __future__ import annotations

import datetime
import unittest
from unittest.mock import patch

from payway.client import Client
from payway.model import BankAccount, PayWayCard, PayWayCustomer, PayWayPayment
from payway.test_utils import load_json_file


class TestCustomerRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        You will need to create a sandbox PayWay account and add your sandbox API keys into your environment
        """

        merchant_id = "TEST"
        bank_account_id = "0000000A"
        publishable_api_key = "TPUBLISHABLE-API-KEY"
        secret_api_key = "TPUBLISHABLE-SECRET"
        cls.client = Client(
            merchant_id=merchant_id,
            bank_account_id=bank_account_id,
            publishable_api_key=publishable_api_key,
            secret_api_key=secret_api_key,
        )
        cls.customer = PayWayCustomer(
            custom_id="c981b",
            customer_name="Jane Smith",
            email_address="janesmith@example.com",
            send_email_receipts=False,  # not available in sandbox
            phone_number="0343232323",
            street="1 Test Street",
            street2="2 Test Street",
            city_name="Sydney",
            state="NSW",
            postal_code="2000",
        )
        cls.card = PayWayCard(
            card_number="4564710000000004",
            cvn="847",
            card_holder_name="Test",
            expiry_date_month="02",
            expiry_date_year="29",
        )
        cls.expired_card = PayWayCard(
            card_number="4564710000000012",
            cvn="963",
            card_holder_name="Test",
            expiry_date_month="02",
            expiry_date_year="15",
        )
        cls.stolen_card = PayWayCard(
            card_number="5163200000000016",
            cvn="728",
            card_holder_name="Test",
            expiry_date_month="12",
            expiry_date_year="29",
        )
        cls.declined_card = PayWayCard(
            card_number="4444333322221111",
            cvn="111",
            card_holder_name="Test",
            expiry_date_month="01",
            expiry_date_year="40",
        )
        cls.payment = PayWayPayment(
            customer_number="",
            transaction_type="payment",
            amount="10",
            currency="aud",
            order_number="5100",
            ip_address="127.0.0.1",
        )
        cls.pre_auth_payment = PayWayPayment(
            customer_number="",
            transaction_type="preAuth",
            amount="2.15",
            currency="aud",
            order_number="5110",
            ip_address="127.0.0.1",
        )
        cls.pre_auth_capture_payment = PayWayPayment(
            transaction_type="capture",
            parent_transaction_id="",
            amount="2.15",
            order_number="5111",
            ip_address="127.0.0.1",
        )
        cls.bank_account = BankAccount(
            account_name="Test",
            bsb="000-000",
            account_number=123456,
        )
        cls.invalid_bank_account = BankAccount(
            account_name="Test",
            bsb="000-001",
            account_number=123456,
        )

    @patch("requests.Session.patch")
    def test_stop_all_payments(self, mock_post) -> None:
        # stop payments for customer
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "stopped": True,
        }
        stop_payment_resp = self.client.stop_all_payments("1")
        stopped = stop_payment_resp.get("stopped")
        self.assertEqual(stopped, True)

    @patch("requests.Session.patch")
    def test_start_all_payments(self, mock_post) -> None:
        # start payments for customer
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "stopped": False,
        }
        payment_resp = self.client.start_all_payments("1")
        stopped = payment_resp.get("stopped")
        self.assertEqual(stopped, False)

    @patch("requests.Session.delete")
    def test_delete_customer(self, mock_post) -> None:
        mock_post.return_value.status_code = 204
        # delete customer record in PayWay
        response = self.client.delete_customer("1")
        self.assertEqual(response.status_code, 204)

    @patch("requests.Session.put")
    def test_schedule_payments(self, mock_post) -> None:
        next_week = datetime.datetime.now() + datetime.timedelta(weeks=1)
        next_payment_date = next_week.strftime("%d %b %Y")
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "frequency": "weekly",
            "nextPaymentDate": next_payment_date,
            "nextPrincipalAmount": 10.50,
            "regularPrincipalAmount": 10.50,
            "regularPaymentAmount": 10.50,
        }
        response = self.client.schedule_payments(
            customer_number="1",
            frequency="weekly",
            next_payment_date=next_payment_date,
            regular_amount=10.50,
        )
        self.assertEqual(response.__class__, dict)
        self.assertEqual(response["frequency"], "weekly")
        self.assertEqual(response["nextPaymentDate"], next_payment_date)
        self.assertEqual(response["nextPrincipalAmount"], 10.50)
        self.assertEqual(response["regularPrincipalAmount"], 10.50)
        self.assertEqual(response["regularPaymentAmount"], 10.50)

    @patch("requests.Session.delete")
    def test_stop_schedule(self, mock_post) -> None:
        # stop schedule
        mock_post.return_value.status_code = 204
        response = self.client.stop_schedule("1")
        self.assertEqual(response.status_code, 204)

    @patch("requests.Session.put")
    def test_update_contact_details(self, mock_post) -> None:
        # update contact details
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "customerName": "Jack Smith",
            "emailAddress": "jacksmith@example.com",
            "phoneNumber": "0353532323",
            "address": {
                "street1": "3 Test St",
                "street2": "Apt 1",
                "cityName": "Melbourne",
                "state": "VIC",
                "postalCode": "3029",
            },
        }
        new_name = "Jack Smith"
        new_email = "jacksmith@example.com"
        new_phone = "0353532323"
        new_street1 = "3 Test St"
        new_street2 = "Apt 1"
        new_city = "Melbourne"
        new_state = "VIC"
        new_postcode = "3029"
        update_details = {
            "customerName": new_name,
            "emailAddress": new_email,
            "phoneNumber": new_phone,
            "street1": new_street1,
            "street2": new_street2,
            "cityName": new_city,
            "state": new_state,
            "postalCode": new_postcode,
        }
        response = self.client.update_contact_details("1", **update_details)
        self.assertEqual(response["customerName"], new_name)
        self.assertEqual(response["emailAddress"], new_email)
        self.assertEqual(response["phoneNumber"], new_phone)
        address = response["address"]
        self.assertEqual(address["street1"], new_street1)
        self.assertEqual(address["street2"], new_street2)
        self.assertEqual(address["cityName"], new_city)
        self.assertEqual(address["state"], new_state)
        self.assertEqual(address["postalCode"], new_postcode)

    @patch("requests.Session.get")
    def test_list_customers(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/customers.json")
        response = self.client.list_customers()
        self.assertEqual(response.__class__, dict)
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.get("data"))
