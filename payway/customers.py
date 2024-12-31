from __future__ import annotations

import requests

from payway.conf import CUSTOMER_URL
from payway.model import PayWayCustomer
from payway.utils import json_list


class CustomerRequest:
    session = requests.Session()
    session_no_headers = requests.Session()

    @json_list("delete_customer")
    def delete_customer(self, customer_number: int) -> requests.Response:
        """
        Returns a list of transactions
        """
        return self.session_no_headers.delete(f"{CUSTOMER_URL}/{customer_number}")

    @json_list("schedule_payments")
    def schedule_payments(
        self,
        customer_number: int,
        frequency: str,
        next_payment_date: str,
        regular_amount: int,
        next_amount: int | None = None,
    ) -> requests.Response:
        """
        Schedule a new payment for a customer
        :param customer_number	PayWay customer number
        :param frequency	weekly, fortnightly, monthly, quarterly, six-monthly, yearly.
        :param next_payment_date	str format `dd MMM yyyy` The date on which the next payment will be collected.
        :param next_amount	Different amount for the next payment (optional).
        :param regular_amount	Usual amount for payments.
        """
        data = {
            "frequency": frequency,
            "nextPaymentDate": next_payment_date,
            "nextPrincipalAmount": next_amount,
            "regularPrincipalAmount": regular_amount,
        }
        return self.session_no_headers.put(
            f"{CUSTOMER_URL}/{customer_number}/schedule",
            data=data,
        )

    @json_list("schedule_payments")
    def stop_schedule(self, customer_number: int) -> requests.Response:
        """
        Stop a schedule for a customer
        """
        return self.session_no_headers.delete(
            f"{CUSTOMER_URL}/{customer_number}/schedule",
        )

    @json_list("stop_all_payments")
    def stop_all_payments(self, customer_number: int) -> requests.Response:
        """
        Stops any new payments using the stored credit card or bank account/
        """
        data = {"stopped": "true"}
        return self.session_no_headers.patch(
            f"{CUSTOMER_URL}/{customer_number}/payment-setup",
            data=data,
        )

    @json_list("start_all_payments")
    def start_all_payments(self, customer_number: int) -> requests.Response:
        """
        Allows any new payments using the stored credit card or bank account.
        """
        data = {"stopped": "false"}
        return self.session_no_headers.patch(
            f"{CUSTOMER_URL}/{customer_number}/payment-setup",
            data=data,
        )

    @json_list("update_contact_details")
    def update_contact_details(self, customer_number: int, customer: PayWayCustomer | None = None, **options: dict) -> requests.Response:
        """
        param: customer_number: PayWay customer number
        param: customer PayWayCustomer object
        param: options customer details
        """
        data = {}
        if customer:
            data.update(customer.to_dict())
        data.update(options)
        return self.session.put(
            f"{CUSTOMER_URL}/{customer_number}/contact",
            data=data,
        )

    @json_list("list_customers")
    def list_customers(self) -> requests.Response:
        """
        List all customers in PayWay
        Returns paginated list of customerNumber, customerName
        """
        # TODO: add page numbers
        return self.session_no_headers.get(CUSTOMER_URL)
