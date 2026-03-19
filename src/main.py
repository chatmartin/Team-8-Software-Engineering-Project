#this file is for frontend-backend communication
from flask import Flask,jsonify,request
from flask_cors import CORS
from globals import *
from account_handling import *

#TODO: Start adding routes to connect with frontend
def create_app(): #This creates a flask app to communicate with the frontend
    app = Flask(__name__)


    return app

if __name__ == '__main__':
    app = create_app()
    CORS(app) #TODO: change to be CORS(app,origins=["https://domainname.com"]) once domain is established to connect to frontend
    app.run(debug=True)
