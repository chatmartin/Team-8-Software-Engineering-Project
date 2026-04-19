#this file is for frontend-backend communication
from flask import Flask,jsonify,request
from flask_cors import CORS
from account_handling import *
from food_tracking import *
from goal_tracking import *
from restrictions import *
from bio_data import *

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

    @app.route('del_account',methods=["DELETE"])
    def del_account():
        data = request.get_json()
        msg = delete_account(data.get('username'))
        return jsonify({"message":msg})

    @app.route('/search',methods=["GET"])
    def search():
        data = request.get_json()
        result = search_meal(data.get('query'),data.get('username'))
        return jsonify({"results":result})

    @app.route('/get_usr_meals',methods=["GET"])
    def get_usr_meals():
        data = request.get_json()
        result = get_meals(data.get('username'))
        return jsonify(result)

    @app.route('/add_usr_meal',methods=["POST"])
    def add_usr_meal():
        data = request.get_json()
        result = add_meal(data.get('username'),data.get('recipe_id'),data.get('eaten_at'))
        return jsonify(result)

    @app.route('/del_usr_meal',methods=["DELETE"])
    def del_usr_meal():
        data = request.get_json()
        result = remove_meal(data.get('username'),data.get('recipe_id'),data.get('eaten_at'))
        return jsonify({"message":result})

    @app.route('/update_usr_meal',methods=["PUT"])
    def update_usr_meal():
        data = request.get_json()
        result = update_meal(data.get('username'),data.get('recipe_id_old'),data.get('recipe_id_new'))
        return jsonify({"message":result})

    @app.route('/update_usr_meal_time',methods=["PUT"])
    def update_usr_meal_time():
        data = request.get_json()
        result = update_meal_time(data.get('username'),data.get('recipe_id'),data.get('eaten_at'))
        return jsonify({"message":result})

    @app.route('/get_usr_goals',methods=["GET"])
    def get_usr_goals():
        data = request.get_json()
        result = get_goals(data.get('username'))
        return jsonify(result)

    @app.route('/add_usr_goal',methods=["POST"])
    def add_usr_goal():
        data = request.get_json()
        result = add_goal(data.get('username'),data.get('nutrient'),data.get('amount'),data.get('min_max'))
        return jsonify({"message":result})

    @app.route('/update_usr_goal',methods=["PUT"])
    def update_usr_goal():
        data = request.get_json()
        result = update_goal(data.get('username'),data.get('nutrient'),data.get('amount'),data.get('min_max'))
        return jsonify({"message":result})

    @app.route('/del_usr_goal',methods=["DELETE"])
    def del_usr_goal():
        data = request.get_json()
        result = remove_goal(data.get('username'),data.get('nutrient'))
        return jsonify({"message":result})

    @app.route('/add_allergy',methods=["POST"])
    def add_allergy():
        data = request.get_json()
        result = add_allergen(data.get('username'),data.get('allergen'),data.get('severity'))
        return jsonify({"message":result})

    @app.route('/del_allergy',methods=["DELETE"])
    def del_allergy():
        data = request.get_json()
        result = remove_allergen(data.get('username'),data.get('allergen'))
        return jsonify({"message":result})

    @app.route('/update_severity',methods=["PUT"])
    def update_severity():
        data = request.get_json()
        result = update_allergen_severity(data.get('username'),data.get('allergen'),data.get('severity'))
        return jsonify({"message":result})

    @app.route('/add_diet',methods=["POST"])
    def add_diet():
        data = request.get_json()
        result = add_restriction(data.get('username'),data.get('restriction'))
        return jsonify({"message":result})

    @app.route('/del_diet',methods=["DELETE"])
    def del_diet():
        data = request.get_json()
        result = remove_restriction(data.get('username'),data.get('restriction'))
        return jsonify({"message":result})

    @app.route('/add_bio',methods=["POST"])
    def add_bio():
        data = request.get_json()
        result = add_bio_data(data.get('username'),data.get('gender'),data.get('height'),data.get('weight'),data.get('body_fat'),data.get('age'))
        return jsonify({"message":result})

    @app.route('update_usr_gender',methods=["PUT"])
    def update_usr_gender():
        data = request.get_json()
        result = update_gender(data.get('username'),data.get('gender'))
        return jsonify({"message":result})

    @app.route('update_usr_height',methods=["PUT"])
    def update_usr_height():
        data = request.get_json()
        result = update_height(data.get('username'),data.get('height'))
        return jsonify({"message":result})

    @app.route('update_usr_weight',methods=["PUT"])
    def update_usr_weight():
        data = request.get_json()
        result = update_weight(data.get('username'),data.get('weight'))
        return jsonify({"message":result})

    @app.route('update_usr_fat',methods=["PUT"])
    def update_usr_fat():
        data = request.get_json()
        result = update_body_fat(data.get('username'),data.get('body_fat'))
        return jsonify({"message":result})

    @app.route('update_usr_age',methods=["PUT"])
    def update_usr_age():
        data = request.get_json()
        result = update_age(data.get('username'),data.get('age'))
        return jsonify({"message":result})

    return app

if __name__ == '__main__':
    get_db_conn()
    flask_app = create_app()
    CORS(flask_app) #TODO: change to be CORS(app,origins=["https://domainname.com"]) once domain is established to connect to frontend
    flask_app.run(debug=True)
