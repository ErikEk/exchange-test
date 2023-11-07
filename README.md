# exchange-test

Test exchange built with tinydb for portability. Would rather use a sql based database 
in an non-assignment environment. The server generates a test template database file (db.json) everytime 
it is restarted with three users (name1, name2, name3), each with a different starting balance denominated
in dollars. 
Call GET '/accounts/' to fetch all accounts.

Prices are randomized (within the given interval) every second from a background process.

Receive a token from '/oauth/token' and add the token though 'Authorize' in swagger as 'Bearer <token>'.

I left out the endpoints '/symbols/ POST' and '/symbols/ PUT' in this example.

Run 'flask run' and access swagger on 'http://127.0.0.1:5000'. The endpoints shown in swagger contains 
example data.
