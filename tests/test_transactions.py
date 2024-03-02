import unittest
from unittest.mock import patch

from payway.client import Client


class TestTransactionRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
    def test_search_transactions(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "transactionId": 1179985404,
                    "receiptNumber": "1179985404",
                    "status": "approved",
                    "responseCode": "11",
                    "responseText": "Approved VIP",
                    "transactionType": "payment",
                    "customerNumber": "1",
                    "customerName": "Po & Sons Pty Ltd",
                    "customerEmail": "henry@example.net",
                    "currency": "aud",
                    "principalAmount": 100.00,
                    "surchargeAmount": 1.00,
                    "paymentAmount": 101.00,
                    "paymentMethod": "creditCard",
                }
            ]
        }
        query = "/search-customer?customerNumber=1"
        response = self.client.search_transactions(query)
        transactions = response["data"]
        self.assertIsNotNone(transactions)
