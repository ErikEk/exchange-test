from flask import Flask, jsonify
from flask_restful import Resource, Api
from flask_swagger_ui import get_swaggerui_blueprint
import json
import jwt
import os
from auth_middleware import token_required

authorizations = {
    "basicAuth" : {
        "type" : "basic"
    }
}


app = Flask(__name__)
api = Api(app)

SECRET_KEY = os.environ.get('SECRET_KEY') or 'set secret message'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['API_VERSION'] = "0.1"

# Define a sample resource
class HelloWorld(Resource):
    def get(self):
        return jsonify({'message': 'Hello, World!'})

# Add the resource to the API
api.add_resource(HelloWorld, '/hello')


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
#@app.doc(security="basicAuth")
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
@token_required
def get_symbols():
    return "asd"


@app.route("/accounts/",methods=['GET'])
@token_required
def get_accounts():
    headers = flask.request.headers
    print(headers.get('Authorization'))
