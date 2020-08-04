# `PayWay REST API Python library`
`Testing`
1. Sign up for a PayWay Sandbox account: https://www.payway.com.au/sandbox
2. Test the integration by adding your PayWay REST API keys to your local environment. These keys are in Account Settings > `REST API Keys`. Copy `Publishable` and `Secret` API keys.
3. export PAYWAY_PUBLISHABLE_API_KEY=[ your PayWay Publishable API Key ]
4. export export PAYWAY_SECRET_API_KEY=[ your PayWay Secret API Key ]
5. Run the tests to ensure the integration is working. 
Run `python -m unittest`

# `Make a transaction`
1. Create a Client class with your PayWay API credentials

`client = Client(merchant_id=merchant_id,
                 bank_account_id=bank_account_id,
                 publishable_api_key=publishable_api_key,
                 secret_api_key=secret_api_key,
                 redirect_url=redirect_url)`
                 
2. Create a Customer class with your customer's details

`customer = Customer(
            custom_id='c981a',
            customer_name='John Smith',
            email_address='johnsmith@example.com',
            send_email_receipts=False,  # not available in sandbox
            phone_number='0343232323',
            street='1 Test Street',
            street2='2 Test Street',
            city_name='Sydney',
            state='NSW',
            postal_code='2000',
        )`
        
3. Create a Card class with your customer's card details

`card = Card(
            card_number='4564710000000004',
            cvn='847',
            card_holder_name='Test',
            expiry_date_month='02',
            expiry_date_year='29'
        )`

4. Create a token from your card (or bank account if direct debit)
`token_response, errors = self.client.create_token(card, 'card')`

`token = token_response.token`        
   
5. Store the customer and their card/bank account token in PayWay
`customer.token = token`

`payway_customer, customer_errors = self.client.create_customer(customer)`

`Note 'payway_customer' object contains full customer response fields from PayWay`
        
6. Create a Payment class with the payment details

`payment = Payment(
            customer_number='',
            transaction_type='payment',
            amount='10',
            currency='aud',
            order_number='5100',
            ip_address='127.0.0.1',
        )`
        
`payment.customer_number = payway_customer.customer_number`

`# optionally assign an order number`

`payment.order_number = '5100'`

6. Process transaction
`transaction, errors = self.client.process_payment(payment)`    
                                 
7. Parse the `transaction` object

`if transaction.status == 'approved':`
`   # process successful response`    

# `Direct Debit`
Direct debit transactions are possible by creating a token from a BankAccount object:

`
bank_account = BankAccount(
            account_name='Test',
            bsb='000-000',
            account_number=123456,
        )
`

`token_response, errors = self.client.create_token(bank_account, 'direct_debit')`

`token = token_response.token`

You would now store the token with the customer in PayWay the same way as the Credit Card method outlined above.

Note: direct debit transactions are not processed initially so must be polled regularly to find the transation result from the customer's bank.

Use the `get_transaction` client method to poll the transaction.
`transaction, errors = self.client.get_transaction(transaction.transaction_id)` 

# `Additional notes`                             

