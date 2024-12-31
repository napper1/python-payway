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
    def test_search_transactions(self, mock_get) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = load_json_file("tests/data/transactions.json")
        query = "/search-customer?customerNumber=1"
        response = self.client.search_transactions(query)
        transactions = response["data"]
        self.assertIsNotNone(transactions)
