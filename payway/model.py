from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BankAccount:
    """
    account_name: str: 	Name used to open bank account.
    bsb: str: bank account BSB
    account_number: str: bank account number
    """

    account_name: str
    bsb: str
    account_number: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "accountName": self.account_name,
            "bsb": self.bsb,
            "accountNumber": self.account_number,
        }


@dataclass
class PayWayCard:
    card_number: str | None = None
    cvn: str | None = None
    card_holder_name: str | None = None
    expiry_date_month: str | None = None
    expiry_date_year: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cardNumber": self.card_number,
            "cvn": self.cvn,
            "cardholderName": self.card_holder_name,
            "expiryDateMonth": self.expiry_date_month,
            "expiryDateYear": self.expiry_date_year,  # Should be YY
        }

    @staticmethod
    def from_dict(payway_card: dict[str, Any]) -> PayWayCard:
        card_number = payway_card.get("maskedCardNumber") or payway_card.get("cardNumber")
        return PayWayCard(
            card_number=card_number,
            cvn=payway_card.get("cvn"),
            card_holder_name=payway_card.get("cardholderName"),
            expiry_date_month=payway_card.get("expiryDateMonth"),
            expiry_date_year=payway_card.get("expiryDateYear"),
        )


@dataclass
class PayWayCustomer:
    custom_id: str | None = None
    customer_name: str | None = None
    email_address: str | None = None
    send_email_receipts: bool | None = None
    phone_number: str | None = None
    street: str | None = None
    street2: str | None = None
    city_name: str | None = None
    state: str | None = None
    postal_code: str | None = None
    token: str | None = None
    customer_number: str | None = None
    payment_setup: PaymentSetup | None = None
    notes: str | None = None
    custom_field_1: str | None = None
    custom_field_2: str | None = None
    custom_field_3: str | None = None
    custom_field_4: str | None = None

    def to_dict(self) -> dict[str, Any]:
        customer = {
            "customerName": self.customer_name,
            "emailAddress": self.email_address,
            "sendEmailReceipts": "true" if self.send_email_receipts else "false",
            "phoneNumber": self.phone_number,
            "street1": self.street,
            "street2": self.street2,
            "cityName": self.city_name,
            "state": self.state,
            "postalCode": self.postal_code,
            "notes": self.notes,
            "customField1": self.custom_field_1,
            "customField2": self.custom_field_2,
            "customField3": self.custom_field_3,
            "customField4": self.custom_field_4,
        }
        if self.token:
            customer.update({"singleUseTokenId": self.token})
        return customer

    @staticmethod
    def from_dict(response: dict[str, Any]) -> PayWayCustomer:
        """
        Parse PayWay Customer response data
        :param response: dict    PayWay response dictionary
        :return:
        """
        contact = response.get("contact", {})
        address = contact.get("address", {})
        payment_setup = None
        if response.get("paymentSetup") is not None:
            payment_setup = PaymentSetup.from_dict(response.get("paymentSetup", {}))
        custom_fields = response.get("customFields", {})
        return PayWayCustomer(
            customer_name=contact.get("customerName"),
            email_address=contact.get("emailAddress"),
            send_email_receipts=contact.get("sendEmailReceipts"),
            phone_number=contact.get("phoneNumber"),
            street=address.get("street1"),
            street2=address.get("street2"),
            city_name=address.get("cityName"),
            state=address.get("state"),
            postal_code=address.get("postalCode"),
            customer_number=response.get("customerNumber"),
            payment_setup=payment_setup,
            notes=response.get("notes"),
            custom_field_1=custom_fields.get("customField1"),
            custom_field_2=custom_fields.get("customField2"),
            custom_field_3=custom_fields.get("customField3"),
            custom_field_4=custom_fields.get("customField4"),
        )


@dataclass
class PaymentError:
    field_name: str | None = None
    message: str | None = None
    field_value: str | None = None

    @staticmethod
    def from_dict(payway_response: dict[str, Any]) -> list[PaymentError]:
        """
        Returns a list of errors from PayWay
        :param: payway_response: dict PayWay response dictionary
        """
        errors = payway_response.get("data", [])
        return [
            PaymentError(
                field_name=error.get("fieldName"),
                message=error.get("message"),
                field_value=error.get("fieldValue"),
            )
            for error in errors
        ]

    def to_message(self) -> str:
        return f"Field: {self.field_name} Message: {self.message} Field Value: {self.field_value}"

    @staticmethod
    def list_to_message(payway_errors: list[PaymentError]) -> str:
        """
        Convert list to readable string
        :param payway_errors:
        :return:
        """
        message = ""
        for error in payway_errors:
            message += error.to_message()
            if len(payway_errors) > 1:
                message += " | "
        return message


@dataclass
class ServerError:
    error_number: int | None = None
    trace_code: str | None = None

    @staticmethod
    def from_dict(response: dict[str, Any]) -> ServerError:
        """
        :param: response: dict PayWay response dictionary
        """
        return ServerError(
            error_number=response.get("errorNumber"),
            trace_code=response.get("traceCode"),
        )

    def to_message(self) -> str:
        return f"Error number: {self.error_number} Trace code: {self.trace_code}"


@dataclass
class PayWayPayment:
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

    transaction_type: str
    customer_number: str | None = None
    amount: float | None = None
    currency: str | None = None
    order_number: str | None = None
    ip_address: str | None = None
    parent_transaction_id: str | None = None
    token: str | None = None
    merchant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payment = {
            "customerNumber": self.customer_number,
            "transactionType": self.transaction_type,  # default to "payment"
            "principalAmount": self.amount,
            "currency": self.currency,
            "orderNumber": self.order_number,  # Max 20 ascii chars
            "customerIpAddress": self.ip_address,
        }
        if self.parent_transaction_id:
            payment["parentTransactionId"] = self.parent_transaction_id
        # fields for pre-authorisation
        if self.token:
            payment["singleUseTokenId"] = self.token
        if self.merchant_id:
            payment["merchantId"] = self.merchant_id
        return payment


@dataclass
class PayWayTransaction:
    transaction_id: int | None = None
    receipt_number: str | None = None
    status: str | None = None
    response_code: str | None = None
    response_text: str | None = None
    transaction_type: str | None = None
    customer_number: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    bpay_ref: str | None = None
    order_number: str | None = None
    currency: str | None = None
    principal_amount: float | None = None
    surcharge_amount: float | None = None
    payment_amount: float | None = None
    payment_method: str | None = None
    declined_date: str | None = None
    card: PayWayCard | None = None
    merchant: Merchant | None = None
    virtual_account: dict[str, Any] | None = None
    australia_post: dict[str, Any] | None = None
    bpay: dict[str, Any] | None = None
    your_bank_account: dict[str, Any] | None = None
    customer_paypal_account: dict[str, Any] | None = None
    your_paypal_account: dict[str, Any] | None = None
    transaction_date_time: str | None = None
    user: dict[str, Any] | None = None
    settlement_date: str | None = None
    parent_transaction: dict[str, Any] | None = None
    ip_address: str | None = None
    fraud_result: str | None = None
    ip_country: str | None = None
    card_country: str | None = None
    custom_fields: dict[str, Any] | None = None
    is_voidable: bool | None = None
    is_refundable: bool | None = None

    def to_dict(self) -> dict[str, Any]:
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
            "creditCard": self.card.to_dict() if self.card is not None else {},
            "merchant": self.merchant.to_dict() if self.merchant is not None else {},
            "virtualAccount": self.virtual_account,
            "australiaPost": self.australia_post,
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
    def from_dict(response: dict[str, Any]) -> PayWayTransaction:
        """
        :param: response: dict PayWay response dictionary
        """
        card = None
        if response.get("creditCard") is not None:
            card = PayWayCard.from_dict(response.get("creditCard", {}))

        merchant = None
        if response.get("merchant") is not None:
            merchant = Merchant.from_dict(response.get("merchant", {}))

        return PayWayTransaction(
            transaction_id=response.get("transactionId"),
            receipt_number=response.get("receiptNumber"),
            status=response.get("status"),
            response_code=response.get("responseCode"),
            response_text=response.get("responseText"),
            transaction_type=response.get("transactionType"),
            customer_number=response.get("customerNumber"),
            customer_name=response.get("customerName"),
            customer_email=response.get("customerEmail"),
            currency=response.get("currency"),
            principal_amount=response.get("principalAmount"),
            surcharge_amount=response.get("surchargeAmount"),
            payment_amount=response.get("paymentAmount"),
            payment_method=response.get("paymentMethod"),
            card=card,
            merchant=merchant,
            virtual_account=response.get("virtualAccount"),
            australia_post=response.get("australiaPost"),
            bpay=response.get("bpay"),
            your_bank_account=response.get("yourBankAccount"),
            customer_paypal_account=response.get("customerPayPalAccount"),
            your_paypal_account=response.get("yourPayPalAccount"),
            transaction_date_time=response.get("transactionDateTime"),
            user=response.get("user"),
            settlement_date=response.get("settlementDate"),
            declined_date=response.get("declinedDate"),
            parent_transaction=response.get("parentTransaction"),
            ip_address=response.get("customerIpAddress"),
            fraud_result=response.get("fraudResult"),
            ip_country=response.get("customerIpCountry"),
            card_country=response.get("cardCountry"),
            custom_fields=response.get("customFields"),
            is_voidable=response.get("isVoidable"),
            is_refundable=response.get("isRefundable"),
        )


@dataclass
class Merchant:
    """
    merchantId 	Issued by us to uniquely identify a merchant facility
    merchantName
    settlementBsb 	The BSB of your settlement bank account
    settlementAccountNumber 	The account number of your settlement bank account
    surchargeBsb 	If surcharges are settled separately, the BSB for your surcharge settlement account
    surchargeAccountNumber 	If surcharges are settled separately, the account number for your surcharge settlement
                            account
    """

    merchant_id: str | None = None
    merchant_name: str | None = None
    settlement_bsb: str | None = None
    settlement_account_number: str | None = None
    surcharge_bsb: str | None = None
    surcharge_account_number: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "merchantId": self.merchant_id,
            "merchantName": self.merchant_name,
            "settlementBsb": self.settlement_bsb,
            "settlementAccountNumber": self.settlement_account_number,
            "surchargeBsb": self.surcharge_bsb,
            "surchargeAccountNumber": self.surcharge_account_number,
        }

    @staticmethod
    def from_dict(payway_obj: dict[str, Any]) -> Merchant:
        """
        :param: payway_obj: dict PayWay response dictionary
        """
        return Merchant(
            merchant_id=payway_obj.get("merchantId"),
            merchant_name=payway_obj.get("merchantName"),
            settlement_bsb=payway_obj.get("settlementBsb"),
            settlement_account_number=payway_obj.get("settlementAccountNumber"),
            surcharge_bsb=payway_obj.get("surchargeBsb"),
            surcharge_account_number=payway_obj.get("surchargeAccountNumber"),
        )


@dataclass
class PaymentSetup:
    payment_method: str | None = None
    stopped: bool | None = None
    credit_card: PayWayCard | None = None
    merchant: Merchant | None = None

    @staticmethod
    def from_dict(response: dict[str, Any]) -> PaymentSetup:
        """
        :param: response: dict PayWay response dictionary
        """
        credit_card = None
        if response.get("creditCard") is not None:
            credit_card = PayWayCard.from_dict(response.get("creditCard", {}))

        merchant = None
        if response.get("merchant") is not None:
            merchant = Merchant.from_dict(response.get("merchant", {}))

        return PaymentSetup(
            payment_method=response.get("paymentMethod"),
            stopped=response.get("stopped"),
            credit_card=credit_card,
            merchant=merchant,
        )


@dataclass
class TokenResponse:
    token: str | None = None
    payment_method: str | None = None
    card: PayWayCard | None = None
    bank_account: dict[str, Any] | None = None

    @staticmethod
    def from_dict(response: dict[str, Any]) -> TokenResponse:
        """
        :param: response: dict PayWay response dictionary
        """
        card = None
        if response.get("creditCard") is not None:
            card = PayWayCard.from_dict(response["creditCard"])

        return TokenResponse(
            token=response.get("singleUseTokenId"),
            payment_method=response.get("paymentMethod"),
            card=card,
        )
