from flask import Flask, jsonify, request
from flask_restful import Api, Resource

from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017") #27017 is a default port used by mongodb
db = client.aNewDB
UserNum = db["UserNum"]

UserNum.insert({
    'num_of_user':0
})

class Visit(Resource):
    def get(self):
        prev_num = UserNum.find({})[0]['num_of_user']
        new_num = prev_num +1 
        UserNum.update({},{"$set":{"num_of_user":new_num}})
        return str("Hello user "+ str(new_num))


def checkPosted(postedData,functionName):
    if(functionName=='add' or functionName == 'sub' or functionName == 'mul'):
        if 'x' not in postedData or 'y' not in postedData:
            return 301
        else:
            return 200
    if(functionName == 'div'):
        if 'x' not in postedData or 'y' not in postedData:
            return 301
        elif postedData['y'] == 0:
            return 302
        else:
            return 200

class Add(Resource):
    def post(self):
        #post
        #Get posted data
        postedData = request.get_json()
        #verify validity of posted data
        status_code = checkPosted(postedData,'add')
        if(status_code != 200):
            retJson = {
                "Message":"An error happened",
                "Status Code": status_code
            }
            return jsonify(retJson)

        x = postedData['x']
        y = postedData['y']
        x = int(x)
        y = int(y)

        #add posted data
        ret =  x+y
        retMap = {
            "Message":ret,
            "Status Code" : 200
        }
        return jsonify(retMap)

class Subtract(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPosted(postedData,'sub')
        if(status_code!=200):
            retJson = {
                "Message": 'An error occured',
                "Status Code": status_code
            }
            return jsonify(retJson)

        x=postedData['x']
        y=postedData['y']
        x= int(x)
        y= int(y)

        ret = x-y
        retMap = {
            "Message":ret,
            "Status Code": 200
        }
        return jsonify(retMap)

class Multiply(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPosted(postedData,'mul')

        if(status_code!=200):
            retJson = {
                "Message": 'An error occured',
                "Status Code": status_code
            }
            return jsonify(retJson)

        x=postedData['x']
        y=postedData['y']
        x= int(x)
        y= int(y)

        ret = x*y
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

class Divide(Resource):
    def post(self):
        postedData = request.get_json()
        status_code = checkPosted(postedData,'div')

        if(status_code!=200):
            retJson = {
                "Message": 'An error occured',
                "Status Code": status_code
            }
            return jsonify(retJson)

        x=postedData['x']
        y=postedData['y']
        x= int(x)
        y= int(y)

        ret = x/y
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

api.add_resource(Add, "/add") #resources is added which is using Add resource and is routed to /add
api.add_resource(Subtract,'/sub')
api.add_resource(Multiply, '/mul')
api.add_resource(Divide,'/div')
api.add_resource(Visit,'/hello')


@app.route('/')
def hello_world():
    return "Hello World!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
