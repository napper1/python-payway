import requests

from payway.conf import CUSTOMER_URL
from payway.utils import json_list


class CustomerRequest(object):
    session = requests.Session()
    session_no_headers = requests.Session()

    @json_list('delete_customer')
    def delete_customer(self, customer_number):
        """
        Returns a list of transactions
        """
        return self.session_no_headers.delete("%s/%s" % (CUSTOMER_URL, customer_number))

    @json_list('schedule_payments')
    def schedule_payments(self, customer_number, frequency, next_payment_date, regular_amount, next_amount=None):
        """
        Schedule a new payment for a customer
        :param customer_number	PayWay customer number
        :param frequency	weekly, fortnightly, monthly, quarterly, six-monthly, yearly.
        :param next_payment_date	str format `dd MMM yyyy` The date on which the next payment will be collected.
        :param next_amount	Different amount for the next payment (optional).
        :param regular_amount	Usual amount for payments.
        """
        data = {
            'frequency': frequency,
            'nextPaymentDate': next_payment_date,
            'nextPrincipalAmount': next_amount,
            'regularPrincipalAmount': regular_amount,
        }
        return self.session_no_headers.put("%s/%s/schedule" % (CUSTOMER_URL, customer_number), data=data)

    @json_list('schedule_payments')
    def stop_schedule(self, customer_number):
        """
        Stop a schedule for a customer
        """
        return self.session_no_headers.delete("%s/%s/schedule" % (CUSTOMER_URL, customer_number))

    @json_list('stop_all_payments')
    def stop_all_payments(self, customer_number):
        """
        Stops any new payments using the stored credit card or bank account/
        """
        data = {
            'stopped': 'true'
        }
        return self.session_no_headers.patch("%s/%s/payment-setup" % (CUSTOMER_URL, customer_number), data=data)

    @json_list('start_all_payments')
    def start_all_payments(self, customer_number):
        """
        Allows any new payments using the stored credit card or bank account.
        """
        data = {
            'stopped': 'false'
        }
        return self.session_no_headers.patch("%s/%s/payment-setup" % (CUSTOMER_URL, customer_number), data=data)

    @json_list('update_contact_details')
    def update_contact_details(self, customer_number, customer=None, **options):
        """
        param: customer_number: PayWay customer number
        param: customer PayWayCustomer object
        param: options customer details
        """
        data = {}
        if customer:
            data.update(customer.to_dict())
        data.update(options)
        return self.session.put("%s/%s/contact" % (CUSTOMER_URL, customer_number), data=data)

    @json_list('list_customers')
    def list_customers(self):
        """
        List all customers in PayWay
        Returns paginated list of customerNumber, customerName
        """
        # TODO: add page numbers
        return self.session_no_headers.get("%s" % CUSTOMER_URL)
