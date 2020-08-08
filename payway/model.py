

class BankAccount(object):
    """
    account_name: str: 	Name used to open bank account.
    bsb: str: bank account BSB
    account_number: str: bank account number
    """

    def __init__(self, account_name, bsb, account_number):
        self.account_name = account_name
        self.bsb = bsb
        self.account_number = account_number

    def to_dict(self):
        return {
            'accountName': self.account_name,
            'bsb': self.bsb,
            'accountNumber': self.account_number
        }


class PayWayCard(object):

    def __init__(self, card_number=None, cvn=None, card_holder_name=None, expiry_date_month=None,
                 expiry_date_year=None):
        self.card_number = card_number
        self.cvn = cvn
        self.card_holder_name = card_holder_name
        self.expiry_date_month = expiry_date_month
        self.expiry_date_year = expiry_date_year

    def to_dict(self):
        return {
            'cardNumber': self.card_number,
            'cvn': self.cvn,
            'cardholderName': self.card_holder_name,
            'expiryDateMonth': self.expiry_date_month,
            'expiryDateYear': self.expiry_date_year  # Should be YY
        }

    @staticmethod
    def from_dict(payway_card):
        card = PayWayCard()
        if payway_card.get("maskedCardNumber"):
            card.card_number = payway_card.get("maskedCardNumber")
        else:
            card.card_number = payway_card.get("cardNumber")
        card.cvn = payway_card.get("cvn")
        card.card_holder_name = payway_card.get("cardholderName")
        card.expiry_date_month = payway_card.get("expiryDateMonth")
        card.expiry_date_year = payway_card.get("expiryDateYear")
        return card


class PayWayCustomer(object):

    def __init__(self, custom_id=None, customer_name=None, email_address=None, send_email_receipts=None,
                 phone_number=None, street=None, street2=None, city_name=None, state=None, postal_code=None,
                 token=None, customer_number=None, payment_setup=None, notes=None, custom_field_1=None,
                 custom_field_2=None, custom_field_3=None, custom_field_4=None):
        self.custom_id = custom_id
        self.customer_name = customer_name
        self.email_address = email_address
        self.send_email_receipts = send_email_receipts
        self.phone_number = phone_number
        self.street = street
        self.street2 = street2
        self.city_name = city_name
        self.state = state
        self.postal_code = postal_code
        self.token = token
        self.customer_number = customer_number
        self.payment_setup = payment_setup
        self.notes = notes
        self.customField1 = custom_field_1
        self.customField2 = custom_field_2
        self.customField3 = custom_field_3
        self.customField4 = custom_field_4

    def to_dict(self):
        return {
            "customerName": self.customer_name,
            "emailAddress": self.email_address,
            "sendEmailReceipts": 'true' if self.send_email_receipts else 'false',
            "phoneNumber": self.phone_number,
            "street1": self.street,
            "street2": self.street2,
            "cityName": self.city_name,
            "state": self.state,
            "postalCode": self.postal_code,
            "singleUseTokenId": self.token,
            "notes": self.notes,
            "customField1": self.customField1,
            "customField2": self.customField2,
            "customField3": self.customField3,
            "customField4": self.customField4,
        }

    @staticmethod
    def from_dict(response):
        """
        Parse PayWay Customer response data
        :param response: dict    PayWay response dictionary
        :return:
        """
        customer = PayWayCustomer()
        contact = response.get("contact")
        customer.customer_name = contact.get("customerName")
        customer.email_address = contact.get("emailAddress")
        customer.send_email_receipts = contact.get("sendEmailReceipts")
        customer.phone_number = contact.get("phoneNumber")
        address = contact.get("address")
        customer.street = address.get("street1")
        customer.street2 = address.get("street2")
        customer.city_name = address.get("cityName")
        customer.state = address.get("state")
        customer.postal_code = address.get("postalCode")
        customer.customer_number = response.get("customerNumber")

        if response.get("paymentSetup") is not None:
            customer.payment_setup = PaymentSetup().from_dict(response.get("paymentSetup"))

        if response.get("customFields") is not None:
            custom_fields = response.get("customFields")
            for k, v in custom_fields.items():
                setattr(customer, k, v)

        if response.get("notes") is not None:
            customer.notes = response['notes']

        return customer


class PaymentError(object):
    field_name = None
    message = None
    field_value = None

    @staticmethod
    def from_dict(payway_response):
        """
        Returns a list of errors from PayWay
        :param: payway_response: dict PayWay response dictionary
        """
        errors = payway_response.get("data")
        payment_errors = []
        for error in errors:
            payway_error = PaymentError()
            payway_error.field_name = error.get("fieldName")
            payway_error.message = error.get("message")
            payway_error.field_value = error.get("fieldValue")
            payment_errors.append(payway_error)
        return payment_errors

    def to_message(self):
        return "Field: {} Message: {} Field Value: {}".format(
            self.field_name, self.message, self.field_value,
        )

    @staticmethod
    def list_to_message(payway_errors):
        """
        Convert list to readable string
        :param payway_errors:
        :return:
        """
        message = ""
        for error in payway_errors:
            message += error.to_message()
            if len(payway_errors) > 1:
                message += ' | '
        return message


class ServerError(object):
    error_number = None
    trace_code = None

    @staticmethod
    def from_dict(response):
        """
        :param: response: dict PayWay response dictionary
        """
        payway_error = ServerError()
        payway_error.error_number = response.get("errorNumber")
        payway_error.trace_code = response.get("traceCode")
        return payway_error

    def to_message(self):
        return "Error number: {} Trace code: {}".format(self.error_number, self.trace_code)


class PayWayPayment(object):
    """
    customer_number: 	Customer to which this payment belongs.
    transaction_type:	payment, refund, preAuth, capture or accountVerification
    amount:	Amount before any surcharge added. Negative for a refund.
    currency: aud
    order_number:	A reference number for this transaction, generated by you.
    ip_address:	IP address your customer used to connect and process the transaction (if applicable).
    parent_transaction_id:	The transactionId of the pre-authorisation
    token:	A token issued by PayWay which holds credit card details. See single use tokens.
    merchant_id: 	This merchant will be used for processing.
    """

    def __init__(self, transaction_type, customer_number=None, amount=None, currency=None, order_number=None,
                 ip_address=None, parent_transaction_id=None, token=None, merchant_id=None):
        self.transaction_type = transaction_type
        self.customer_number = customer_number
        self.amount = amount
        self.currency = currency
        self.order_number = order_number
        self.ip_address = ip_address
        self.parent_transaction_id = parent_transaction_id
        self.token = token
        self.merchant_id = merchant_id

    def to_dict(self):
        payment = {
            "customerNumber": self.customer_number,
            "transactionType": self.transaction_type,  # default to "payment"
            "principalAmount": self.amount,
            "currency": self.currency,
            "orderNumber": self.order_number,  # Max 20 ascii chars
            "customerIpAddress": self.ip_address,
        }
        if self.parent_transaction_id:
            payment['parentTransactionId'] = self.parent_transaction_id
        # fields for pre-authorisation
        if self.token:
            payment['singleUseTokenId'] = self.token
        if self.merchant_id:
            payment['merchantId'] = self.merchant_id
        return payment


class PayWayTransaction(object):
    transaction_id = None
    receipt_number = None
    status = None
    response_code = None
    response_text = None
    transaction_type = None
    customer_number = None
    customer_name = None
    customer_email = None
    bpay_ref = None
    order_number = None
    currency = None
    principal_amount = None
    surcharge_amount = None
    payment_amount = None
    payment_method = None
    declined_date = None
    card = None
    merchant = None
    virtual_account = None
    australia_post = None
    bpay = None
    your_bank_account = None
    customer_paypal_account = None
    your_paypal_account = None
    transaction_date_time = None
    user = None
    settlement_date = None
    parent_transaction = None
    ip_address = None
    fraud_result = None
    ip_country = None
    card_country = None
    custom_fields = None
    is_voidable = None
    is_refundable = None

    def to_dict(self):
        return {
            "transactionId": self.transaction_id,
            "receiptNumber": self.receipt_number,
            "status": self.status,
            "responseCode": self.response_code,
            "responseText": self.response_text,
            "transactionType": self.transaction_type,
            "customerNumber": self.customer_number,
            "customerName": self.customer_name,
            "customerEmail": self.customer_email,
            "currency": self.currency,
            "principalAmount": self.principal_amount,
            "surchargeAmount": self.surcharge_amount,
            "paymentAmount": self.payment_amount,
            "paymentMethod": self.payment_method,
            "creditCard": self.card.to_dict(),
            "merchant": self.merchant.to_dict(),
            "virtualAccount": self.virtual_account,
            "bpaustraliaPostay": self.australia_post,
            "bpay": self.bpay,
            "yourBankAccount": self.your_bank_account,
            "customerPayPalAccount": self.customer_paypal_account,
            "yourPayPalAccount": self.your_paypal_account,
            "transactionDateTime": self.transaction_date_time,
            "user": self.user,
            "settlementDate": self.settlement_date,
            "declinedDate": self.declined_date,
            "parentTransaction": self.parent_transaction,
            "customerIpAddress": self.ip_address,
            "fraudResult": self.fraud_result,
            "customerIpCountry": self.ip_country,
            "cardCountry": self.card_country,
            "customFields": self.custom_fields,
            "isVoidable": self.is_voidable,
            "isRefundable": self.is_refundable,
        }

    @staticmethod
    def from_dict(response):
        """
        :param: response: dict PayWay response dictionary
        """
        transaction = PayWayTransaction()
        transaction.transaction_id = response.get('transactionId')
        transaction.receipt_number = response.get("receiptNumber")
        transaction.status = response.get("status")
        transaction.response_code = response.get("responseCode")
        transaction.response_text = response.get("responseText")
        transaction.transaction_type = response.get("transactionType")
        transaction.customer_number = response.get("customerNumber")
        transaction.customer_name = response.get("customerName")
        transaction.customer_email = response.get("customerEmail")
        transaction.currency = response.get("currency")
        transaction.principal_amount = response.get("principalAmount")
        transaction.surcharge_amount = response.get("surchargeAmount")
        transaction.payment_amount = response.get("paymentAmount")
        transaction.payment_method = response.get("paymentMethod")

        if response.get("creditCard") is not None:
            transaction.card = PayWayCard.from_dict(response.get("creditCard"))

        if response.get("merchant") is not None:
            transaction.merchant = Merchant.from_dict(response.get("merchant"))

        transaction.virtual_account = response.get("virtualAccount")
        transaction.australia_post = response.get("bpaustraliaPostay")
        transaction.bpay = response.get("bpay")
        transaction.your_bank_account = response.get("yourBankAccount")
        transaction.customer_paypal_account = response.get("customerPayPalAccount")
        transaction.your_paypal_account = response.get("yourPayPalAccount")
        transaction.transaction_date_time = response.get("transactionDateTime")
        transaction.user = response.get("user")
        transaction.settlement_date = response.get("settlementDate")
        transaction.declined_date = response.get("declinedDate")
        transaction.parent_transaction = response.get("parentTransaction")
        transaction.ip_address = response.get("customerIpAddress")
        transaction.fraud_result = response.get("fraudResult")
        transaction.ip_country = response.get("customerIpCountry")
        transaction.card_country = response.get("cardCountry")
        transaction.custom_fields = response.get("customFields")
        transaction.is_voidable = response.get("isVoidable")
        transaction.is_refundable = response.get("isRefundable")
        return transaction


class Merchant(object):
    """
    merchantId 	Issued by us to uniquely identify a merchant facility
    merchantName
    settlementBsb 	The BSB of your settlement bank account
    settlementAccountNumber 	The account number of your settlement bank account
    surchargeBsb 	If surcharges are settled separately, the BSB for your surcharge settlement account
    surchargeAccountNumber 	If surcharges are settled separately, the account number for your surcharge settlement
                            account
    """
    merchant_id = None
    merchant_name = None
    settlement_bsb = None
    settlement_account_number = None
    surcharge_bsb = None
    surcharge_account_number = None

    def to_dict(self):
        return {
            'merchantId': self.merchant_id,
            'merchantName': self.merchant_name,
            'settlementBsb': self.settlement_bsb,
            'settlementAccountNumber': self.settlement_account_number,
            'surchargeBsb': self.surcharge_bsb,
            'surchargeAccountNumber': self.surcharge_account_number,
        }

    @staticmethod
    def from_dict(payway_obj):
        """
        :param: payway_obj: dict PayWay response dictionary
        """
        merchant = Merchant()
        merchant.merchant_id = payway_obj.get("merchantId")
        merchant.merchant_name = payway_obj.get('merchantName')
        merchant.settlement_bsb = payway_obj.get('settlementBsb')
        merchant.settlement_account_number = payway_obj.get('settlementAccountNumber')
        merchant.surcharge_bsb = payway_obj.get('surchargeBsb')
        merchant.surcharge_account_number = payway_obj.get('surchargeAccountNumber')
        return merchant


class PaymentSetup(object):
    payment_method = None
    stopped = None
    credit_card = None
    merchant = None

    @staticmethod
    def from_dict(response):
        """
        :param: response: dict PayWay response dictionary
        """
        ps = PaymentSetup()
        ps.payment_method = response.get("paymentMethod")
        ps.stopped = response.get("stopped")
        if response.get("creditCard") is not None:
            ps.credit_card = PayWayCard().from_dict(response.get("creditCard"))
        if response.get("merchant") is not None:
            ps.merchant = Merchant().from_dict(response.get("merchant"))
        return ps


class TokenResponse(object):
    token = None
    payment_method = None
    card = None
    bank_account = None

    @staticmethod
    def from_dict(response):
        """
        :param: response: dict PayWay response dictionary
        """
        tr = TokenResponse()
        tr.token = response.get("singleUseTokenId")
        tr.payment_method = response.get("paymentMethod")
        if response.get("creditCard") is not None:
            card = PayWayCard().from_dict(response["creditCard"])
            tr.card = card
        return tr
