from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_swagger_ui import get_swaggerui_blueprint
import json
import jwt
import os
from auth_middleware import token_required
from tinydb import TinyDB, Query
from apscheduler.schedulers.background import BackgroundScheduler
import random
import uuid

# Load database
db = TinyDB('./db.json')
Prices = Query()
Accounts = Query()
Trade = Query()

# insert test data...
prices =  [
    {'symbol': 'EURUSD', 'price': 1.04},
    {'symbol': 'BTCUSD', 'price': 24000}
]
accounts =  [
    {'login': 'name1', 'password': "asd", 'enable': True, 'email': 'name1@gmail.com', 'balance': 100},
    {'login': 'name2', 'password': "asd", 'enable': True, 'email': 'name2@gmail.com', 'balance': 1000},
    {'login': 'name3', 'password': "asd", 'enable': False, 'email': 'name3@gmail.com', 'balance': 10000},
]
prices_table = db.table('prices')
prices_table.truncate() # Clear old price data (for test purposes)
accounts_table = db.table('accounts')
accounts_table.truncate() # Clear old user data (for test purposes)
trades_table = db.table('trades')
trades_table.truncate() # Clear old trades data (for test purposes)

# Insert new data
prices_table.insert_multiple(prices)
accounts_table.insert_multiple(accounts)

def update_prices():
    # Set random prices.
    prices_table = db.table('prices')
    eurusd = random.randint(104, 106) / 100
    btcusd = random.randint(24000, 30000)
    prices_table.update({'price': eurusd},Prices.symbol == 'EURUSD')
    prices_table.update({'price': btcusd},Prices.symbol == 'BTCUSD')

# Initiate the api instance
app = Flask(__name__)
api = Api(app)

# Update the prices every sec in the background.
with app.app_context():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_prices, 'interval', seconds=1)
    scheduler.start()

SECRET_KEY = os.environ.get('SECRET_KEY') or 'set secret message!'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['API_VERSION'] = "0.1"

# Configure Swagger UI
SWAGGER_URL = '/swagger'
API_URL = 'http://127.0.0.1:5000/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Sample API",
        
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL, )

@app.route('/swagger.json')
def swagger():
    with open('swagger.json', 'r') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(debug=True)

@app.route("/.version")
@token_required
def get_version():
    return jsonify({'api_version': app.config['API_VERSION']})

@app.route("/oauth2/token")
def get_oauth2token():
    try:
        token = jwt.encode(
            {"user_id": "manager_id"},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return {
            "message": "Successfully fetched manager auth token",
            "token": token
        }
    except Exception as e:
                return {
                    "error": "cound not fetch manager auth token",
                    "message": str(e)
                }, 500

@app.route("/symbols/",methods=['GET'])
@token_required
def get_symbols():

    return jsonify([
         {
            "symbol": "BTCUSD",
            "description": "Bitcoin/usd symbol",
         },
         {
            "symbol": "EURUSD",
            "description": "Euro/usd symbol",
         },
    ])

@app.route("/quotes/<string:symbol>/",methods=['GET'])
@token_required
def get_quotes(symbol):
    symbol = prices_table.get(Prices.symbol == symbol)
    return jsonify([
         {
            "symbol": symbol['symbol'],
            "ask": symbol['price']*1.01, # asking price 1% above bid.
            "bid": symbol['price'],
         },
    ])

@app.route("/accounts/",methods=['GET'])
@token_required
def get_accounts():
    accounts = db.table("accounts")
    return jsonify(accounts.all())

@app.route("/accounts/",methods=['POST'])
@token_required
def post_accounts():
    account = request.json
    # Make sure unique login.
    if accounts_table.search(Accounts.login == account["login"]):
        return jsonify({
            "message": "account with same name already exists",
        }), 500
    
    accounts_table.insert(account)
    return jsonify({
        "message": "successfully retrieved user profile",
        "data": account
    })

@app.route("/accounts/",methods=['PUT'])
@token_required
def put_accounts():
    account = request.json
    login = account['login']

    # Make sure login account exists.
    if not accounts_table.search(Accounts.login == login):
        return jsonify({
            "message": "account was not found",
        }), 500
    
    accounts_table.update({'password': account['password'],
                           'enable': account['enable'],
                           'email': account['email'],
                           'balance': account['balance']},
                           Accounts.login == login)
    return jsonify({
        "message": "successfully updated account",
        "data": account
    })

@app.route("/trades/",methods=['POST'])
#@token_required
def post_trades():
    order = request.json


    accounts = accounts_table.search(Accounts.login == order['login'])
    # Make sure account exists.
    if len(accounts) < 1:
        return jsonify({
            "message": "account not found",
        })
    account = accounts[0]

    symbol = prices_table.get(Prices.symbol == order['symbol'])

    if order['operation'] == 'buy':

        # Here we would take a 1% cut from the spread.
        order_size = order['volume']*symbol['price']*1.01

        # Check if there is enough balance on the account
        if account['balance'] < order_size:
            return jsonify({
                "message": "not enough balance",
            })
        print(f"Bought {order_size} {order['symbol']}!!")

        new_balance = account['balance']-order_size
        
        accounts_table.update({'balance': new_balance},
                            Accounts.login == account['login'])
        account['balance'] = new_balance

        # Assign unique id. TODO: Check if id really is unique.
        order.update({'id': str(uuid.uuid4())})

        trades_table.insert(order)

        return jsonify({
            "message": "successfully updated a trade",
            "trade": order
        })
    elif order['operation'] == 'sell':
        trades = trades_table.search((Trade.login == order['login']) & (Trade.symbol == order['symbol']))
        if len(trades) < 1:
            return jsonify({
                "message": "could not find any trades",
            })
        print(trades)

    return jsonify({
        "message": "no trade done"
    })


@app.route("/trades/close/<string:id>",methods=['POST'])
#@token_required
def post_trades_close(id):

    trades = trades_table.search(Trade.id == id)
    if len(trades) < 1:
        return jsonify({
            "message": "trade id not found",
        })
    trade = trades[0]

    # Put in function
    accounts = accounts_table.search(Accounts.login == trade['login'])
    # Make sure account exists.
    if len(accounts) < 1:
        return jsonify({
            "message": "account not found",
        })
    account = accounts[0]

    print(trade)
    if trade['operation'] == 'buy':
        price = prices_table.get(Prices.symbol == trade['symbol'])
        print(price)
        amount_sold = price['price']*trade['volume']
        new_balance = account['balance'] + amount_sold
        accounts_table.update({'balance': new_balance},
                            Accounts.login == trade['login'])

    # Remove trade entry from database for simplicity.
    ok = trades_table.remove(Trade.id == id)

    return jsonify({
            "message": "successfully closed a trade",
            "trade": trade
        })

