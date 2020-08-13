import requests

from payway.conf import TRANSACTION_URL
from payway.utils import json_list


class TransactionRequest(object):
    session = requests.Session()
    session_no_headers = requests.Session()

    @json_list('search_transactions')
    def search_transactions(self, query):
        """
        Returns a list of transactions
        """
        return self.session_no_headers.get(TRANSACTION_URL + query)
