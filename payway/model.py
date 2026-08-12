from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Self

from payway.utils import snake_to_camel


class PayWayModel:
    """
    Mixin for dataclasses: to_dict/from_dict mapping snake_case fields to
    PayWay's camelCase keys, driven by the dataclass fields.

    Field metadata keys:
        alias:      PayWay key when it is not the camelCase of the field name
        exclude:    omit the field from to_dict output
        from_dict:  callable applied to a non-None raw value when parsing

    Instances built by from_dict keep the response body they were parsed from
    on ``raw``, unchanged. Parsing is lossy - undeclared PayWay keys are dropped,
    absent ones become None, and aliases rename them - so callers persisting a
    response for auditing or dispute resolution should store ``raw``, not
    ``to_dict()``. Models you build yourself leave it None.
    """

    __dataclass_fields__: ClassVar[dict[str, Any]]
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for f in fields(self):
            if f.metadata.get("exclude"):
                continue
            value = getattr(self, f.name)
            if isinstance(value, PayWayModel):
                value = value.to_dict()
            result[f.metadata.get("alias", snake_to_camel(f.name))] = value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        kwargs = {}
        for f in fields(cls):
            value = data.get(f.metadata.get("alias", snake_to_camel(f.name)))
            converter = f.metadata.get("from_dict")
            if converter is not None and value is not None:
                value = converter(value)
            kwargs[f.name] = value
        instance = cls(**kwargs)
        instance.raw = data
        return instance


@dataclass
class BankAccount(PayWayModel):
    """
    account_name: str: 	Name used to open bank account.
    bsb: str: bank account BSB
    account_number: str: bank account number
    """

    account_name: str
    bsb: str
    account_number: str


@dataclass
class PayWayCard(PayWayModel):
    card_number: str | None = None
    cvn: str | None = None
    card_holder_name: str | None = field(default=None, metadata={"alias": "cardholderName"})
    expiry_date_month: str | None = None
    expiry_date_year: str | None = None  # Should be YY

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PayWayCard:
        card = super().from_dict({**data, "cardNumber": data.get("maskedCardNumber") or data.get("cardNumber")})
        # Keep PayWay's own body, not the copy rewritten for the alias above.
        card.raw = data
        return card


@dataclass
class Merchant(PayWayModel):
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


@dataclass
class PaymentSetup(PayWayModel):
    payment_method: str | None = None
    stopped: bool | None = None
    credit_card: PayWayCard | None = field(default=None, metadata={"from_dict": PayWayCard.from_dict})
    merchant: Merchant | None = field(default=None, metadata={"from_dict": Merchant.from_dict})


@dataclass
class PayWayCustomer(PayWayModel):
    custom_id: str | None = field(default=None, metadata={"exclude": True})
    customer_name: str | None = None
    email_address: str | None = None
    send_email_receipts: bool | None = None
    phone_number: str | None = None
    street: str | None = field(default=None, metadata={"alias": "street1"})
    street2: str | None = None
    city_name: str | None = None
    state: str | None = None
    postal_code: str | None = None
    token: str | None = field(default=None, metadata={"alias": "singleUseTokenId"})
    customer_number: str | None = field(default=None, metadata={"exclude": True})
    payment_setup: PaymentSetup | None = field(default=None, metadata={"exclude": True})
    notes: str | None = None
    custom_field_1: str | None = None
    custom_field_2: str | None = None
    custom_field_3: str | None = None
    custom_field_4: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["sendEmailReceipts"] = "true" if self.send_email_receipts else "false"
        if not self.token:
            del data["singleUseTokenId"]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PayWayCustomer:
        """
        Parse PayWay Customer response data: contact and address are nested
        in the response but flat on this model.
        """
        contact = data.get("contact", {})
        address = contact.get("address", {})
        payment_setup = None
        if data.get("paymentSetup") is not None:
            payment_setup = PaymentSetup.from_dict(data.get("paymentSetup", {}))
        custom_fields = data.get("customFields", {})
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
            customer_number=data.get("customerNumber"),
            payment_setup=payment_setup,
            notes=data.get("notes"),
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
class ServerError(PayWayModel):
    error_number: int | None = None
    trace_code: str | None = None

    def to_message(self) -> str:
        return f"Error number: {self.error_number} Trace code: {self.trace_code}"


@dataclass
class PayWayPayment(PayWayModel):
    """
    customer_number: 	Customer to which this payment belongs.
    transaction_type:	payment, refund, preAuth, capture or accountVerification
    amount:	Amount before any surcharge added. Negative for a refund.
    currency: aud
    order_number:	A reference number for this transaction, generated by you. Max 20 ascii chars.
    ip_address:	IP address your customer used to connect and process the transaction (if applicable).
    parent_transaction_id:	The transactionId of the pre-authorisation
    token:	A token issued by PayWay which holds credit card details. See single use tokens.
    merchant_id: 	This merchant will be used for processing.
    """

    transaction_type: str
    customer_number: str | None = None
    amount: float | None = field(default=None, metadata={"alias": "principalAmount"})
    currency: str | None = None
    order_number: str | None = None
    ip_address: str | None = field(default=None, metadata={"alias": "customerIpAddress"})
    parent_transaction_id: str | None = None
    token: str | None = field(default=None, metadata={"alias": "singleUseTokenId"})
    merchant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        for key in ("parentTransactionId", "singleUseTokenId", "merchantId"):
            if not data[key]:
                del data[key]
        return data


@dataclass
class PayWayTransaction(PayWayModel):
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
    card: PayWayCard | None = field(default=None, metadata={"alias": "creditCard", "from_dict": PayWayCard.from_dict})
    merchant: Merchant | None = field(default=None, metadata={"from_dict": Merchant.from_dict})
    virtual_account: dict[str, Any] | None = None
    australia_post: dict[str, Any] | None = None
    bpay: dict[str, Any] | None = None
    your_bank_account: dict[str, Any] | None = None
    customer_paypal_account: dict[str, Any] | None = field(default=None, metadata={"alias": "customerPayPalAccount"})
    your_paypal_account: dict[str, Any] | None = field(default=None, metadata={"alias": "yourPayPalAccount"})
    transaction_date_time: str | None = None
    user: dict[str, Any] | None = None
    settlement_date: str | None = None
    parent_transaction: dict[str, Any] | None = None
    ip_address: str | None = field(default=None, metadata={"alias": "customerIpAddress"})
    fraud_result: str | None = None
    ip_country: str | None = field(default=None, metadata={"alias": "customerIpCountry"})
    card_country: str | None = None
    custom_fields: dict[str, Any] | None = None
    is_voidable: bool | None = None
    is_refundable: bool | None = None


@dataclass
class TokenResponse(PayWayModel):
    token: str | None = field(default=None, metadata={"alias": "singleUseTokenId"})
    payment_method: str | None = None
    card: PayWayCard | None = field(default=None, metadata={"alias": "creditCard", "from_dict": PayWayCard.from_dict})
    bank_account: dict[str, Any] | None = None
