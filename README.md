# exchange-test

Test exchange built with tinydb for portability. Would rather use a sql based database in an non-test 
environment. The server generates a test template database file (db.json) everytime it is restarted 
with three users (name1, name2, name2) each with a different starting balance. Use GET '/accounts/' 
to fetch them.

Prices are randomized every second within the given price interval.

Receive token from '/oauth/token' and import token though 'Authorize' as 'Bearer <token>'.

I left out the endpoints '/symbols/ POST' and '/symbols/ PUT' in this example.

Run 'flask run' and access swagger on 'http://127.0.0.1:5000'. The endpoints shown in swagger include 
example data.

// Erik Ek