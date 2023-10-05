# exchange-test

Test exchange built with tinydb for portability. Would rather use a sql based database in an non-test 
environment. The server generates a test template database file (db.json) everytime it is restarted 
with three users (name1, name2, name2) each with a different balance.

Receive token from '/oauth/token' and import token though 'Authorize' as 'Bearer <token>'.