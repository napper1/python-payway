from __future__ import annotations

import unittest
from unittest.mock import patch

from payway.client import Client
from payway.test_utils import load_json_file


class TestTransactionRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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

    @patch("requests.Session.get")
    def test_search_transactions_by_customer(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/transactions.json")
        response = self.client.search_transactions_by_customer(1)
        mock_get.assert_called_once_with(
            "https://api.payway.com.au/rest/v1/transactions/search-customer",
            params={"customerNumber": 1, "page": None},
        )
        self.assertIsNotNone(response["data"])

    @patch("requests.Session.get")
    def test_search_transactions_by_customer_with_page(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/transactions.json")
        self.client.search_transactions_by_customer(1, page=2)
        mock_get.assert_called_once_with(
            "https://api.payway.com.au/rest/v1/transactions/search-customer",
            params={"customerNumber": 1, "page": 2},
        )

    @patch("requests.Session.get")
    def test_search_transactions_by_receipt(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/transactions.json")
        response = self.client.search_transactions_by_receipt("1234567")
        mock_get.assert_called_once_with(
            "https://api.payway.com.au/rest/v1/transactions/search-receipt",
            params={"receiptNumber": "1234567", "page": None},
        )
        self.assertIsNotNone(response["data"])

    @patch("requests.Session.get")
    def test_search_transactions_by_order(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/transactions.json")
        response = self.client.search_transactions_by_order("ORDER-1")
        mock_get.assert_called_once_with(
            "https://api.payway.com.au/rest/v1/transactions/search-order",
            params={"orderNumber": "ORDER-1", "page": None},
        )
        self.assertIsNotNone(response["data"])
