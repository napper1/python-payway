# `PayWay REST API - Python`

What this library does:
- Store customers, a card or bank account in PayWay
- Take payment using a stored card or bank account
- Capture a pre-authorisation
- Void transactions
- Refund transactions
- Lookup or poll transactions
- Update a customer's payment setup in PayWay

Testing
1. Sign up for a PayWay Sandbox account: https://www.payway.com.au/sandbox
2. Test the integration by adding your PayWay REST API keys to your local environment. These keys are in Account Settings > `REST API Keys`. Copy `Publishable` and `Secret` API keys.
3. `export PAYWAY_PUBLISHABLE_API_KEY=[ your PayWay Publishable API Key ]`
4. `export PAYWAY_SECRET_API_KEY=[ your PayWay Secret API Key ]`
5. Run the tests to ensure the integration is working. 
`python -m unittest`

# `Make a transaction`

Create a Client class with your PayWay API credentials

```
from payway.model import *
from payway.client import *

client = Client(merchant_id=merchant_id,
                bank_account_id=bank_account_id,
                publishable_api_key=publishable_api_key,
                secret_api_key=secret_api_key,
                redirect_url=redirect_url)
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

Create a token from your card (or bank account if direct debit)

`token_response, errors = client.create_card_token(card)`

`token = token_response.token`        
   
Store the customer and their card/bank account token in PayWay

`customer.token = token`

`payway_customer, customer_errors = client.create_customer(customer)`

Note the 'payway_customer' object contains the full customer response fields from PayWay.
        
Create a Payment class with the payment details

```
customer_number = payway_customer.customer_number
payment = Payment(customer_number=customer_number,
                  transaction_type='payment',
                  amount='10',
                  currency='aud',
                  order_number='5100',
                  ip_address='127.0.0.1')
```

Process transaction

`transaction, errors = client.process_payment(payment)`    
                                 
Check the `transaction` for the result

`if transaction.status == 'approved':`

`   # process successful response`    

# `Direct Debit`
Direct debit transactions are possible by creating a token from a bank account:

```
bank_account = BankAccount(account_name='Test', bsb='000-000', account_number=123456)
```

`token_response, errors = client.create_bank_account_token(bank_account)`

`token = token_response.token`

Store the token with a customer in PayWay using the same methods as the Card outlined above.

Note: direct debit transactions take days to process so must be polled regularly to find the transaction result from the customer's bank.

Poll a transaction using the `get_transaction` method.

`transaction, errors = client.get_transaction(transaction.transaction_id)` 

# `Additional notes`                             
PayWay API documentation
https://www.payway.com.au/docs/rest.html

It is recommended to use PayWay's Trusted Frame https://www.payway.com.au/docs/rest.html#trusted-frame
when creating a single use token of a card or bank account so your PCI-compliance scope is reduced.  

# `Fraud`

Please follow PayWay's advice about reducing your risk of fraudulent transactions.
https://www.payway.com.au/docs/card-testing.html#card-testing
