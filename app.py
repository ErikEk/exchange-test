from flask import Flask, jsonify
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
db = TinyDB('./prices_db.json')
# Clear db
db.truncate()
Prices = Query()
symbols =  [
    {'symbol': 'EURUSD', 'price': 1.04},
    {'symbol': 'BTCUSD', 'price': 24000}
]

db.insert_multiple(symbols)


def readlines():
    table = db.table('user')
    eurusd = random.randint(104, 106) / 100
    btcusd = random.randint(24000, 30000)
    db.update({'price': eurusd},Prices.symbol == 'EURUSD')
    db.update({'price': btcusd},Prices.symbol == 'BTCUSD')


app = Flask(__name__)
api = Api(app)

with app.app_context():
    scheduler = BackgroundScheduler()
    scheduler.add_job(readlines, 'interval', seconds=1)
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
        # token should expire after 24 hrs
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
    print(request.args.get('symbol'))
    btcusd = db.get(Prices.symbol == 'BTCUSD')
    
    #print(db.get(Prices.Symbol == 'EURUSD'))
    return str(btcusd['price'])


@app.route("/accounts/",methods=['GET'])
@token_required
def get_accounts():
    print("asd")


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