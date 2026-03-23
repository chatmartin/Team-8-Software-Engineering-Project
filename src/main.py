#this file is for frontend-backend communication
from flask import Flask,jsonify,request
from flask_cors import CORS
from globals import *
from account_handling import *
from food_tracking import *

def create_app(): #This creates a flask app to communicate with the frontend
    app = Flask(__name__)

    @app.route('/')
    def index():
        return #TODO: change this to return render_template("file.html") once html is made

    @app.route('/create_acc',methods=["POST"])
    def create_acc():
        data = request.get_json()
        email = data.get('email')
        if email == "":
            email = None
        msg = create_account(data.get('username'),data.get('password'),email)
        return jsonify({"message":msg})

    @app.route('/login',methods=["POST"])
    def signin():
        data = request.get_json()
        msg = login(data.get('username'),data.get('password'))
        return jsonify({"message":msg})

    #TODO: This may need some changing if we add email verification or requiring password input/other checking
    @app.route('/new_email', methods=["PUT"])
    def new_email():
        data = request.get_json()
        msg = update_email(data.get('username'),data.get('email'))
        return jsonify({"message":msg})

    @app.route('/get_usr_meals',methods=["GET"])
    def get_usr_meals():
        data = request.get_json()
        result = get_meals(data.get('username'))
        return jsonify(result)

    @app.route('/add_usr_meal',methods=["POST"])
    def add_usr_meal():
        data = request.get_json()
        result = add_meal(data.get('username'),data.get('meal'),data.get('eaten_at'))
        return jsonify(result)

    @app.route('/del_usr_meal',methods=["DELETE"])
    def del_usr_meal():
        data = request.get_json()
        result = remove_meal(data.get('meal_id'))
        return jsonify({"message":result})

    @app.route('/update_usr_meal',methods=["PUT"])
    def update_usr_meal():
        data = request.get_json()
        result = update_meal(data.get('meal_id'),data.get('meal'),data.get('eaten_at'))

    return app

if __name__ == '__main__':
    get_db_conn()
    app = create_app()
    CORS(app) #TODO: change to be CORS(app,origins=["https://domainname.com"]) once domain is established to connect to frontend
    app.run(debug=True)
