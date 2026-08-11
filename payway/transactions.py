from __future__ import annotations

from typing import Any

import requests

from payway.constants import TRANSACTION_URL
from payway.utils import json_list


class TransactionRequest:
    session = requests.Session()
    session_no_headers = requests.Session()

    def _search(self, path: str, params: dict[str, Any]) -> requests.Response:
        return self.session_no_headers.get(f"{TRANSACTION_URL}/{path}", params=params)

    @json_list("search_transactions_by_customer")
    def search_transactions_by_customer(self, customer_number: int | str, page: int | None = None) -> requests.Response:
        """
        Returns a paginated list of transactions for a PayWay customer, most recent first
        :param customer_number: PayWay customer number
        :param page: page number, taken from the `next`/`prev` links of a previous response
        """
        return self._search("search-customer", {"customerNumber": customer_number, "page": page})

    @json_list("search_transactions_by_receipt")
    def search_transactions_by_receipt(self, receipt_number: int | str, page: int | None = None) -> requests.Response:
        """
        Returns a paginated list of transactions with the given receipt number, most recent first
        :param receipt_number: PayWay receipt number
        :param page: page number, taken from the `next`/`prev` links of a previous response
        """
        return self._search("search-receipt", {"receiptNumber": receipt_number, "page": page})

    @json_list("search_transactions_by_order")
    def search_transactions_by_order(self, order_number: str, page: int | None = None) -> requests.Response:
        """
        Returns a paginated list of transactions with the given order number, most recent first
        :param order_number: your order number, supplied when the transaction was created
        :param page: page number, taken from the `next`/`prev` links of a previous response
        """
        return self._search("search-order", {"orderNumber": order_number, "page": page})
