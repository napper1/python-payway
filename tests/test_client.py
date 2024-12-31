from __future__ import annotations

import copy
import unittest
from typing import NoReturn
from unittest.mock import patch

from payway.client import Client
from payway.model import (
    BankAccount,
    PayWayCard,
    PayWayCustomer,
    PayWayPayment,
    PayWayTransaction,
)
from payway.test_utils import load_json_file


class TestClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> NoReturn:
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
            customer_name="John Smith",
            email_address="johnsmith@example.com",
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
            account_number="123456",
        )
        cls.invalid_bank_account = BankAccount(
            account_name="Test",
            bsb="000-001",
            account_number="123456",
        )

    @patch("requests.post")
    def test_create_token(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "singleUseTokenId": "2bcec36f-7b02-43db-b3ec-bfb65acfe272",
            "paymentMethod": "creditCard",
        }

        card = self.card
        token_response, errors = self.client.create_card_token(card)

        self.assertIsNotNone(token_response.token)
        self.assertEqual(token_response.token, "2bcec36f-7b02-43db-b3ec-bfb65acfe272")

    @patch("requests.post")
    def test_create_bank_account_token(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "singleUseTokenId": "3bcec36f-7b02-43db-b3ec-bfb65acfe272",
            "paymentMethod": "bankAccount",
        }
        bank_account = self.bank_account
        token_response, errors = self.client.create_bank_account_token(bank_account)
        token = token_response.token
        self.assertIsNotNone(token)
        self.assertEqual(token, "3bcec36f-7b02-43db-b3ec-bfb65acfe272")

    @patch("requests.post")
    def test_create_customer(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = load_json_file("tests/data/customer.json")
        card = self.card
        token_response, errors = self.client.create_card_token(card)
        customer = self.customer
        customer.token = token_response.token
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        self.assertEqual(payway_customer_number, "98")
        self.assertEqual(payway_customer.customer_name, "Rebecca Turing")
        self.assertEqual(payway_customer.email_address, "bect@example.net")

    @patch("requests.put")
    def test_create_customer_with_custom_id(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = load_json_file("tests/data/customer.json")
        customer = copy.deepcopy(self.customer)
        customer.custom_id = "a123"
        customer.token = "1234"
        payway_customer, customer_errors = self.client.create_customer(customer)
        payway_customer_number = payway_customer.customer_number
        self.assertIsNotNone(payway_customer_number)
        self.assertEqual(payway_customer_number, "98")

    @patch("requests.post")
    def test_process_payment(self, mock_post) -> NoReturn:
        # Take payment (using a credit card token)
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = load_json_file("tests/data/transaction.json")
        payment = copy.deepcopy(self.payment)
        payment.customer_number =  "1"
        payment.token = "2bcec36f-7b02-43db-b3ec-bfb65acfe272"
        payment.order_number = "5200"
        payment.merchant_id = self.client.merchant_id
        transaction, errors = self.client.process_payment(payment)

        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertIsNone(errors)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertIsNotNone(transaction.receipt_number)
        self.assertEqual(transaction.status, "approved")
        self.assertEqual(transaction.response_code, "11")

    @patch("requests.post")
    def test_process_payment_with_idempotency_key(self, mock_post) -> NoReturn:
        """
        Send a payment using a unique idempotency key to try and avoid duplicate POSTs
        https://www.payway.com.au/docs/rest.html#avoiding-duplicate-posts
        """
        mock_post.return_value.status_code = 200
        # load json file
        mock_post.return_value.json.return_value = load_json_file("tests/data/transaction.json")
        customer_number = "1"
        payment = copy.deepcopy(self.payment)
        payment.customer_number = customer_number
        payment.token = "2bcec36f-7b02-43db-b3ec-bfb65acfe272"
        payment.order_number = "5200"
        payment.merchant_id = self.client.merchant_id
        idempotency_key = "f223179b-da1d-474b-a6fc-b78bc429f76d"
        transaction, errors = self.client.process_payment(
            payment,
            idempotency_key=idempotency_key,
        )
        self.assertIsInstance(transaction, PayWayTransaction)
        self.assertIsNone(errors)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertIsNotNone(transaction.receipt_number)
        self.assertEqual(transaction.status, "approved")
        self.assertEqual(transaction.response_code, "11")

    @patch("requests.get")
    def test_get_transaction_card(self, mock_get) -> NoReturn:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/card_transaction.json")
        transaction, errors = self.client.get_transaction(
            1179985404,
        )
        self.assertIsNotNone(transaction)
        self.assertIsNotNone(transaction.transaction_id)
        self.assertEqual(transaction.transaction_id, 1179985404)

    @patch("requests.post")
    def test_void(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = load_json_file("tests/data/void_transaction.json")
        void_transaction, void_errors = self.client.void_transaction(1179985404)
        self.assertIsNone(void_errors)
        self.assertIsNotNone(void_transaction)
        self.assertEqual(void_transaction.status, "voided")

    @patch("requests.post")
    def test_refund(self, mock_post) -> NoReturn:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = load_json_file("tests/data/refund_transaction.json")
        transaction, errors = self.client.refund_transaction(
            transaction_id="1179985404",
            amount="100",
        )
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "refunded")

    @patch("requests.get")
    def test_get_customer(self, mock_get) -> NoReturn:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/customer.json")
        customer, customer_errors = self.client.get_customer("98")
        self.assertIsNotNone(customer)
        self.assertIsNone(customer_errors)
        self.assertEqual(customer.customer_number, "98")
        self.assertEqual(customer.customer_name, "Rebecca Turing")

    @patch("requests.put")
    def test_update_payment_setup_card(self, mock_post) -> NoReturn:
        # update card or bank account in PayWay from token
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "stopped": False,
            "paymentMethod": "creditCard",
        }
        ps, ps_errors = self.client.update_payment_setup(
            token="4bcec36f-7b02-43db-b3ec-bfb65acfe272",
            customer_id="1",
        )
        self.assertIsNone(ps_errors)
        self.assertIsNotNone(ps)
