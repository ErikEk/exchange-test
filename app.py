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

# Load database
db = TinyDB('./db.json')
db.truncate()
Prices = Query()
Accounts = Query()

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

# Insert new data
prices_table.insert_multiple(prices)
accounts_table.insert_multiple(accounts)

def update_prices():
    prices_table = db.table('prices')
    eurusd = random.randint(104, 106) / 100
    btcusd = random.randint(24000, 30000)
    prices_table.update({'price': eurusd},Prices.symbol == 'EURUSD')
    prices_table.update({'price': btcusd},Prices.symbol == 'BTCUSD')

app = Flask(__name__)
api = Api(app)

# Update the prices every sec in the background.
with app.app_context():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_prices, 'interval', seconds=1)
    scheduler.start()

SECRET_KEY = os.environ.get('SECRET_KEY') or 'set secret message'
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
            "message": "Successfully fetched auth token",
            "token": token
        }
    except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500

@app.route("/symbols/",methods=['GET'])
#@token_required
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
#@token_required
def get_quotes(symbol):
    symbol = db.get(Prices.symbol == symbol)
    return jsonify([
         {
            "symbol": symbol['symbol'],
            "ask": symbol['price']*1.01, # ask price 1% more expensive.
            "bid": symbol['price'],
         },
    ])


@app.route("/accounts/",methods=['GET'])
#@token_required
def get_accounts():
    accounts = db.table("accounts")
    return jsonify(accounts.all())

@app.route("/accounts/",methods=['POST'])
#@token_required
def post_accounts():
    accounts = db.table("accounts")
    account = request.json
    print(account)
    #accounts.insert(acount)
    return jsonify({
        "message": "successfully retrieved user profile",
        "data": account
    })


@app.route("/users/", methods=["GET"])
@token_required
def get_current_user(current_user):
    return jsonify({
        "message": "successfully retrieved user profile",
        "data": current_user
    })

@app.route("/users/", methods=["PUT"])
@token_required
def update_user(current_user):
    try:
        user = request.json
        if user.get("name"):
            user = User().update(current_user["_id"], user["name"])
            return jsonify({
                "message": "successfully updated account",
                "data": user
            }), 201
        return {
            "message": "Invalid data, you can only update your account name!",
            "data": None,
            "error": "Bad Request"
        }, 400
    except Exception as e:
        return jsonify({
            "message": "failed to update account",
            "error": str(e),
            "data": None
        }), 400

@app.route("/users/", methods=["DELETE"])
@token_required
def disable_user(current_user):
    try:
        User().disable_account(current_user["_id"])
        return jsonify({
            "message": "successfully disabled acount",
            "data": None
        }), 204
    except Exception as e:
        return jsonify({
            "message": "failed to disable account",
            "error": str(e),
            "data": None
        }), 400