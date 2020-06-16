from flask import Flask,request, jsonify
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://db:27017')
db = client.BankAPI
users = db['Users']

def UserExist(username):
    if users.find({'Username':username}).count()==0:
        return False
    else:
        return True

def generatedJson(status,msg):
    retJson = {
        'status':status,
        'Message':msg
    }
    return retJson

def verifyPw(username,password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        'Username':username
    })[0]['Password']

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)==hashed_pw:
        return True
    else:
        return False

def cashWithUser(username):
    cash = users.find({
        'Username':username
    })[0]['Own']
    return cash

def debtWithUser(username):
    debt = users.find({
        'Username':username
    })[0]['Debt']
    return debt

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']

        if UserExist(username):
            return jsonify(generatedJson(301,'Invalid Username'))
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        users.insert({
            'Username':username,
            'Password':hashed_pw,
            'Own':0,
            'Debt':0
        })

        return jsonify(generatedJson(200,'Successfully signed up for the API!'))

#Tuple - ErrorDictionary, True or False.
# True meaning that there is some error and false meaning that there isn't
def verifyCred(username,password):
    if not UserExist(username):
        return generatedJson(301,'Invalid Username'), True

    correct_pw = verifyPw(username,password)
    if not correct_pw:
        return generatedJson(302,'Incorrect Password'), True

    return None, False

def updateCash(username,balance):
    users.update({
        'Username':username
    },{
        '$set':{
            'Own':balance
        }
    })

def updateDebt(username,balance):
    users.update({
        'Username':username
    },{
        '$set':{
            'Debt':balance
        }
    })

class Add(Resource):
    def post(self):
        postedData= request.get_json()

        username = postedData['username']
        password = postedData['password']
        money = postedData['amount']
        
        retJson, error = verifyCred(username,password)

        if error:
            return jsonify(retJson)
        
        if money<=0:
            return jsonify(generatedJson(304,'The money amount entered must be greater than zero'))
        
        cash = cashWithUser(username)
        money-=1
        bank_cash = cashWithUser('BANK')
        updateCash("BANK",bank_cash+1)
        updateCash(username,cash+money)

        return jsonify(generatedJson(200,'Amount added successfully to account'))

class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        to = postedData['to']
        money = postedData['amount']

        retJson, error = verifyCred(username,password)

        if error:
            return jsonify(retJson)
        
        cash = cashWithUser(username)
        if cash<=0:
            return jsonify(generatedJson(304,'Insufficient funds, please add or take a loan'))
        
        if not UserExist(to):
            return jsonify(generatedJson(301,'Receiver username is invalid'))

        if cash < money:
            return jsonify(generatedJson(304,'Insufficient funds, please add or take a loan'))

        cash_from = cashWithUser(username)
        cash_to = cashWithUser(to)
        bank_cash = cashWithUser("BANK")

        updateCash("BANK",bank_cash+1)
        updateCash(to,cash_to+money-1)
        updateCash(username,cash_from-money)

        return jsonify(generatedJson(200,'Amount transferred successfully!'))

class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']

        retJson,error = verifyCred(username,password)

        if error:
            return jsonify(retJson)

        retJson = users.find({
            'Username':username
        },{
            'Password': 0, #omits the projection of the password field
            '_id': 0 #omits the _id field
        })[0]

        return jsonify(retJson)

class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        money = postedData['amount']

        retJson,error = verifyCred(username,password)
        if error:
            return jsonify(retJson)
        
        cash = cashWithUser(username)
        debt = debtWithUser(username)
        updateCash(username, cash+money)
        updateDebt(username, debt+money)

        return jsonify(generatedJson(200,'Loan added to you account!'))

class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData['username']
        password = postedData['password']
        money = postedData['amount']

        retJson,error = verifyCred(username,password)

        if error:
            return jsonify(retJson)
        
        cash = cashWithUser(username)

        if cash< money:
            return jsonify(generatedJson(303,"Insufficient funds in your account"))
        
        debt = debtWithUser(username)

        updateCash(username,cash-money)
        updateDebt(username,debt-money)

        return jsonify(generatedJson(200,'You have successfully paid your loan'))

api.add_resource(Register,'/register')
api.add_resource(Add,'/add')
api.add_resource(Transfer,'/transfer')
api.add_resource(Balance,'/balance')
api.add_resource(TakeLoan,'/takeloan')
api.add_resource(PayLoan,'/payloan')

if __name__=='__main__':
    app.run(host='0.0.0.0')


