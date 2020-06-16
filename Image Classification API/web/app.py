from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageRecognition
users = db['Users']

def UserExist(username):
    if users.find({'Username':username}).count ==0:
        return False
    else:
        return True

def verify_pw(username,password):
    if not UserExist(username):
        return False
    
    hashed_pw = users.find({
        'Username':username
    })[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)== hashed_pw:
        return True
    else:
        return False

def verifyCredentials(username,password):
    if not UserExist(username):
        return generateReturnDictionary(301,'User does not exit'), True

    correct_pw = verify_pw(username,password)
    if not correct_pw:
        return generateReturnDictionary(302,'Invalid Password'), True
    
    return None,False

def generateReturnDictionary(status,msg):
    retJson = {
        'status':status,
        'Message':msg
    }
    return retJson

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']

        if UserExist(username):
            retJson = {
                'status':301,
                'Message':'Invalid Username'
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            'Username':username,
            'Password':hashed_pw,
            'Tokens':5
        })

        retJson={
            'status':200,
            'Message':'You successfully signed up for the API!'
        }

class Classify(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        url = postedData['url']

        retJson, error = verifyCredentials(username,password)
        if error:
            return jsonify(retJson)
        
        tokens = users.find({
            'Username':username
        })[0]['Tokens']

        if tokens<=0:
            return jsonify(generateReturnDictionary(303,"Not enough Tokens!"))

        r = requests.get(url)
        retJson = {}
        with open('temp.jpg','wb') as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg')
            proc.communicate()[0]
            proc.wait()
            with open('text.txt') as g:
                retJson = json.load(g)
        
        users.update({
            'Username':username
        },{
            '$set':{
                "Tokens":tokens-1
            }
        })
        return retJson
        
class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['admin_pw']
        refill_amt = postedData['refill']

        if not UserExist(username):
            return jsonify(generateReturnDictionary(301,'User does not exist!'))
        
        correct_pw = 'admin'

        if not password==correct_pw:
            return jsonify(generateReturnDictionary(304,'Invalid admin password'))
        
        users.update({
            'Username':username
        },{
            '$set':{
                'Tokens':refill_amt
            }
        })

        return jsonify(generateReturnDictionary(200,'Refilled successfully'))

api.add_resource(Register,'/register')
api.add_resource(Classify,'/classify')
api.add_resource(Refill,'/refill')

if __name__== "__main__":
    app.run(host= '0.0.0.0')

