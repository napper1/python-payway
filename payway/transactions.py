from __future__ import annotations

import requests

from payway.conf import TRANSACTION_URL
from payway.utils import json_list


class TransactionRequest:
    session = requests.Session()
    session_no_headers = requests.Session()

    @json_list("search_transactions")
    def search_transactions(self, query: str) -> requests.Response:
        """
        Returns a list of transactions
        """
        return self.session_no_headers.get(TRANSACTION_URL + query)
