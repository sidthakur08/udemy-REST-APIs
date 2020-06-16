from flask import Flask, jsonify,request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017") #27017 is a default port used by mongodb
db = client.SentencesDatabase
users = db['Users']

def verifyPw(username,password):
    hashed_pw = users.find({
        "Username":username
    })[0]['Password']
    if bcrypt.hashpw(password.encode('utf-8'),hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username":username
    })[0]['Tokens']
    return tokens

class Register(Resource):
    def post(self):
        #step 1: to get posted data by the user
        postedData = request.get_json()
        
        #get the data
        username = postedData['username']
        password = postedData['password']

        #hash(password + salt)
        hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        #store username and pw into the database
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Sentence": "",
            "Tokens": 6
        })

        retJson = {
            "Message":"You successfully signed up for the API",
            "status": 200
        }

        return jsonify(retJson)
        
class Store(Resource):
    def post(self):
        #get posted data
        postedData = request.get_json()

        #read data
        username = postedData['username']
        password = postedData['password']
        sentence = postedData['sentence']

        #verify username password match
        correct_pw = verifyPw(username,password)

        if not correct_pw:
            retJson = {
                "Message":"Incorrect password",
                "status":302
            }
            return jsonify(retJson)
        #verify user has enough tokens
        num_tokens = countTokens(username)
        if num_tokens<=0:
            retJson = {
                "Message": "Out of tokens!",
                "status": 301
            }
            return jsonify(retJson)
        #store sentence, take one token away and return 200 ok
        users.update({
            "Username":username,
        },{
            "$set":{
                "Sentence":sentence,
                "Tokens":num_tokens-1
                }
        })

        retJson = {
            "Message":"Sentence saved successfully!",
            "status": 200
        }

        return jsonify(retJson)

class Get(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData['password']

        correct_pw = verifyPw(username,password)
        if not correct_pw:
            retJson = {
                "Message":"Password is incorrect",
                "Status":302
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)
        if num_tokens<=0:
            retJson= {
                "Message":"Out of Tokens",
                "status":301
            }
            return jsonify(retJson)
        
        users.update({
            "Username":username,
        },{
            "$set":{
                "Tokens":num_tokens-1
                }
        })

        sentence = users.find({
            "Username":username
        })[0]['Sentence']

        retJson = {
            "sentence":sentence,
            "status":200
        }
        return jsonify(retJson)

api.add_resource(Register,'/register')
api.add_resource(Store,'/store')
api.add_resource(Get,'/get')

@app.route('/')
def hello_world():
    return "Hello User!"

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug = True)