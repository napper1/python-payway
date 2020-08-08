# `PayWay REST API - Python`

What this library does:
- Store customers, their card and bank account in PayWay
- Take payment using a stored credit card or bank account
- Process and Capture a pre-authorisation
- Lookup or poll transactions
- Refund transactions
- Void transactions
- Update a customer's payment setup in PayWay

Testing
1. Sign up for a PayWay sandbox account: https://www.payway.com.au/sandbox
2. Test the integration by adding your PayWay REST API keys to your local environment. These keys are in Account Settings > `REST API Keys`. Copy your `Publishable` and `Secret` API keys.
3. `export PAYWAY_PUBLISHABLE_API_KEY="your PayWay Publishable API Key"`
4. `export PAYWAY_SECRET_API_KEY="your PayWay Secret API Key"`
5. Run the tests to ensure the integration is working. 
`python -m unittest tests`

# `Make a transaction`

Create a Client class with your PayWay API credentials

```
from payway.model import *
from payway.client import *

client = Client(merchant_id='',
                bank_account_id='',
                publishable_api_key='',
                secret_api_key='')
```
                 
Create a Customer class with your customer's details

```
customer = Customer(custom_id='c981a',
                    customer_name='John Smith',
                    email_address='johnsmith@example.com',
                    send_email_receipts=False,  # not available in sandbox
                    phone_number='0343232323',
                    street='1 Test Street',
                    street2='2 Test Street',
                    city_name='Sydney',
                    state='NSW',
                    postal_code='2000')
```
        
Create a Card class with your customer's card details

```
card = Card(card_number='4564710000000004',
            cvn='847',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='29')
```

Create a token from your card and create a customer in PayWay

```
token_response, errors = client.create_card_token(card)
token = token_response.token        
customer.token = token
payway_customer, customer_errors = client.create_customer(customer)
```

Note the 'payway_customer' object contains the full customer response fields from PayWay.
        
Create a Payment class with the payment details and process the transaction

```
customer_number = payway_customer.customer_number
payment = Payment(customer_number=customer_number,
                  transaction_type='payment',
                  amount='10',
                  currency='aud',
                  order_number='5100',
                  ip_address='127.0.0.1')
transaction, errors = client.process_payment(payment)
```    
                                 
Check the `transaction` for the result

```
if not errors and transaction.status == 'approved':
    # process successful response
```

# `Handling errors`

Documented errors (such as 422 Unprocessable entity) are parsed into an PaymentError class that you can use in an customer error message.
https://www.payway.com.au/docs/rest.html#http-response-codes

```
if errors:
    for error in errors: 
        print(error.field_name)
        print(error.message) 
        print(error.field_name)
    # or use a method
    PaymentError().list_to_message(errors) 
```     

# `Direct Debit`
Direct debit transactions are possible by creating a token from a bank account:

```
bank_account = BankAccount(account_name='Test', bsb='000-000', account_number=123456)
token_response, errors = client.create_bank_account_token(bank_account)
token = token_response.token
```

Store the token with a customer in PayWay using the same process as the card outlined above.

Note: direct debit transactions take days to process so they must be polled regularly for the latest transaction status from the customer's bank.

# `Lookup transaction`

Poll a transaction using the `get_transaction` method.

```
transaction, errors = client.get_transaction(transaction.transaction_id)
``` 

# `Process and capture a pre-authorisation`

To process a credit card pre-authorisation using a credit card stored against a customer use `preAuth` as the `transaction_type` along with the customer's PayWay number, amount and currency.

```
pre_auth_payment = Payment(
            customer_number='',
            transaction_type='preAuth',
            amount='',
            currency='aud',
            order_number='',
            ip_address='')
transaction, errors = client.process_payment(pre_auth_payment)
```

To capture the pre-authorisation supply a pre-authorisation transaction ID,  `capture` as the `transaction_type` along with an amount to capture.

```
capture_payment = Payment(
            transaction_type='capture',
            parent_transaction_id='',
            amount='',
            order_number='',
            ip_address='')
transaction, errors = client.process_payment(capture_payment)
```

# `Refunds`

Refund a transaction by supplying a transaction ID and the refund amount.

```
refund, errors = client.refund_transaction(
    transaction_id=transaction.transaction_id,
    amount=transaction.principal_amount,
)
```

# `Voiding a transaction`

Void a transaction by supplying a PayWay transaction ID.

```
void_transaction, errors = client.void_transaction(transaction.transaction_id)
```

# `Update Payment Setup`

Update a customer's payment setup with a new credit card or bank account in PayWay. Supply the new token and an existing PayWay customer number.

```
payment_setup, errors = client.update_payment_setup(new_token, payway_customer.customer_number)
```

# `Additional notes`                             
PayWay API documentation
https://www.payway.com.au/docs/rest.html

It is recommended to use PayWay's Trusted Frame https://www.payway.com.au/docs/rest.html#trusted-frame
when creating a single use token of a card or bank account so your PCI-compliance scope is reduced.  

# `Fraud`

Please follow PayWay's advice about reducing your risk of fraudulent transactions.
https://www.payway.com.au/docs/card-testing.html#card-testing
