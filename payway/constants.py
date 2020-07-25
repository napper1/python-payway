from __future__ import unicode_literals


TRANSACTION_APPROVED = '0'

SUMMARY_CODES = {
    TRANSACTION_APPROVED: 'Transaction Approved',
    '1': 'Transaction Declined',
    '2': 'Transaction Erred',
    '3': 'Transaction Rejected',
}

EFT_RESPONSE_CODES = {
    '00': 'Approved or completed successfully',
    '01': 'Refer to card issuer',
    '03': 'Invalid merchant',
    '04': 'Pick-up card',
    '05': 'Do not honour',
    '08': 'Honour with identification',
    '12': 'Invalid transaction',
    '13': 'Invalid amount',
    '14': 'Invalid card number (no such number)',
    '30': 'Format error',
    '36': 'Restricted card',
    '41': 'Lost card',
    '42': 'No universal account',
    '43': 'Stolen card, pick up',
    '51': 'Not sufficient funds',
    '54': 'Expired card',
    '61': 'Exceeds withdrawal amount limits',
    '62': 'Restricted card',
    '65': 'Exceeds withdrawal frequency limit',
    '91': 'Issuer or switch is inoperative',
    '92': 'Financial institution or intermediate network facility cannot be found for routing',
    '94': 'Duplicate transmission',
    'Q1': 'Unknown Buyer',
    'Q2': 'Transaction Pending',
    'Q3': 'Payment Gateway Connection Error',
    'Q4': 'Payment Gateway Unavailable',
    'Q5': 'Invalid Transaction',
    'Q6': 'Duplicate Transaction - requery to determine status',
    'QA': 'Invalid parameters or Initialisation failed',
    'QB': 'Order type not currently supported',
    'QC': 'Invalid Order Type',
    'QD': 'Invalid Payment Amount - Payment amount less than minimum/exceeds maximum allowed limit',
    'QE': 'Internal Error',
    'QF': 'Transaction Failed',
    'QG': 'Unknown Customer Order Number',
    'QH': 'Unknown Customer Username or Password',
    'QI': 'Transaction incomplete - contact Westpac to confirm reconciliation',
    'QJ': 'Invalid Client Certificate',
    'QK': 'Unknown Customer Merchant',
    'QL': 'Business Group not configured for customer',
    'QM': 'Payment Instrument not configured for customer',
    'QN': 'Configuration Error',
    'QO': 'Missing Payment Instrument',
    'QP': 'Missing Supplier Account',
    'QQ': 'Invalid Credit Card \ Invalid Credit Card Verification Number',
    'QR': 'Transaction Retry',
    'QS': 'Transaction Successful',
    'QT': 'Invalid currency',
    'QU': 'Unknown Customer IP Address',
    'QV': 'Invalid Original Order Number specified for Refund, Refund amount exceeds capture amount, or Previous capture was not approved',
    'QW': 'Invalid Reference Number',
    'QX': 'Network Error has occurred',
    'QY': 'Card Type Not Accepted',
    'QZ': 'Zero value transaction',
}

CVN_RESPONSE_CODES = {
    'M': 'Matched',  # i.e. the CVN is correct
    'N': 'Not Matched',  # i.e. the CVN is incorrect
    'P': 'Not Processed',  # i.e. the CVN was not processed for some reason; do not assume that the CVN is necessarily correct
    'S': 'Suspicious',
    'U': 'Unknown',  # i.e. the CVN was not processed for some reason; do not assume that the CVN is necessarily correct
}

CARD_SCHEMES = {
    'AMEX': 'American Express',
    'BANKCARD': 'Bank Card',
    'DINERS': 'Diners Club',
    'MASTERCARD': 'MasterCard',
    'VISA': 'VISA',
}

ECI_CHOICES = {
    'CCT': 'Call Centre Transaction',
    'IVR': 'IVR Transaction',
    'MTO': 'MOTO Transaction',
    'SSL': 'Channel Encrypted Transaction (SSL or other)',
    'REC': 'Recurring payment',
    '5': '3D Secure transaction',
    '6': '3D Secure transaction',
    '7': '3D Secure transaction',
}

APPROVED_TRANSACTION_STATUS = "approved"
APPROVED_CONDITIONAL_TRANSACTION_STATUS = "approved*"
DECLINED_TRANSACTION_STATUS = "declined"
PENDING_TRANSACTION_STATUS = "pending"
VOID_TRANSACTION_STATUS = "voided"
SUSPENDED_TRANSACTION_STATUS = "suspended"

TRANSACTION_STATUS_CHOICES = (
    (APPROVED_TRANSACTION_STATUS, "Approved"),
    (APPROVED_CONDITIONAL_TRANSACTION_STATUS, "Approved*"),
    (PENDING_TRANSACTION_STATUS, "Pending"),
    (DECLINED_TRANSACTION_STATUS, "Declined"),
    (VOID_TRANSACTION_STATUS, "Voided"),
    (SUSPENDED_TRANSACTION_STATUS, "Suspended"),
)

TRANSACTION_TYPE_CHOICES = (
    ("payment", "Payment"),
    ("refund", "Refund"),
    ("preAuth", "Pre-Authorisation"),
)

CREDIT_CARD_PAYMENT_CHOICE = "creditCard"
BANK_ACCOUNT_PAYMENT_CHOICE = "bankAccount"

OTHER_PAYMENT_CHOICES = (
    (CREDIT_CARD_PAYMENT_CHOICE, "Credit Card"),
    ("payPal", "PayPal"),
)

DIRECT_DEBIT_CHOICES = (
    (BANK_ACCOUNT_PAYMENT_CHOICE, "Bank Account"),
    ("bpay", "BPAY"),
    ("australiaPost", "Australia Post"),
    ("westpacBranch", "Westpac Branch"),
    ("remittanceProcessingService", "Remittance Processing Service"),
)
PAYMENT_METHOD_CHOICES = OTHER_PAYMENT_CHOICES + DIRECT_DEBIT_CHOICES
VALID_PAYMENT_METHOD_CHOICES = ['card', 'direct_debit']
