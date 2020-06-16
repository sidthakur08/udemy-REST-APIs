from flask import Flask,jsonify,request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017") #connecting to the db in the local folder with default port
db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    if users.find({'Username':username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']

        if UserExist(username):
            retJson = {
                'status':301,
                'Message':'Username already taken!'
            }
            return jsonify(retJson)
        
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username":username,
            "Password":hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "status":200,
            "Message":"You have successfully signed up to the API!"
        }

        return jsonify(retJson)

def verifyPw(username,password):
    hashed_pw = users.find({
        "Username":username
    })[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        'Username':username
    })[0]['Tokens']
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        text1 = postedData['text1']
        text2 = postedData['text2']

        if not UserExist(username):
            retJson = {
                'status':301,
                'Message':"Invalid Username!"
            }
            return jsonify(retJson)

        correct_pw = verifyPw(username,password)
        if not correct_pw:
            retJson = {
                'status':302,
                'Message':"Incorrect Password!"
            }
            return jsonify(retJson)
        
        num_tokens = countTokens(username)
        if num_tokens<=0:
            retJson = {
                'status':303,
                'Message':'Out of Tokens!'
            }
            return jsonify(retJson)

        #calculate the edit distance
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        #Ratio is a number between 0 and 1. The closer to 1, the more similar the texts are
        sim_ratio = text1.similarity(text2)

        current_tokens = countTokens(username)
        users.update({
            'Username':username,
        },{
            '$set':{
                "Tokens":current_tokens-1
            }
        })

        retJson = {
            'status':200,
            'Similarity':sim_ratio,
            'Message':'Similarity score calculated successfully!'
        }

        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['admin_pw']
        refill_amt = postedData['refill']

        if not UserExist(username):
            retJson = {
                'status':301,
                'Message':'Invalid Username!'
            }
            return jsonify(retJson)
        
        correct_pw = 'admin'

        if not password == correct_pw:
            retJson = {
                'status':304,
                'Message':'Invalid Admin password!'
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)
        users.update({
            'Username':username
        },{
            '$set':{
                'Tokens':refill_amt+current_tokens
            }
        })

        retJson = {
            'status':200,
            'Message':'Tokens refilled successfully'
        }

        return jsonify(retJson)

api.add_resource(Register,'/register')
api.add_resource(Detect,'/detect')
api.add_resource(Refill,'/refill')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
