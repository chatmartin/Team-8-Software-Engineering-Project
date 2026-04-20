"""Flask route definitions for the Ctrl+Eat backend."""

from flask import Flask, jsonify, request
from flask_cors import CORS

from .account_handling import create_account, delete_account, login, update_email
from .bio_data import (
    add_bio_data,
    get_bio_data,
    update_activity,
    update_age,
    update_body_fat,
    update_gender,
    update_height,
    update_weight,
)
from .chat import chat_with_model
from .food_tracking import add_meal, get_meals, remove_meal, search_meal, update_meal, update_meal_time
from .globals import close_db, fail, ok
from .goal_tracking import add_goal, daily_nutrient_progress, get_goals, remove_goal, update_goal, weekly_nutrient_progress
from .recommendations import get_recommendations, save_recommendation_feedback
from .restrictions import (
    add_allergen,
    add_restriction,
    get_preferences,
    remove_allergen,
    remove_restriction,
    update_allergen_severity,
)
from .standard_goals import recommended_goal


def _payload():
    data = request.get_json(silent=True)
    if data is None:
        data = request.args.to_dict()
    return data


def _json(result):
    payload, status = result
    return jsonify(payload), status


def _search_response(query, username):
    if not query:
        return fail("Search query is required.")
    results = search_meal(query, username)
    if results is None:
        return fail("Recipe search is unavailable. Check database and Spoonacular configuration.", 503)
    return ok("Search completed successfully.", results)


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.teardown_appcontext(close_db)

    @app.route("/")
    def index():
        return _json(ok("Ctrl+Eat backend is running.", {"service": "ctrl-eat-backend"}))

    @app.route("/health")
    def health():
        return _json(ok("Healthy.", {"service": "ctrl-eat-backend"}))

    @app.route("/create_acc", methods=["POST"])
    def create_acc():
        data = _payload()
        email = data.get("email") or None
        return _json(create_account(data.get("username"), data.get("password"), email))

    @app.route("/login", methods=["POST"])
    def signin():
        data = _payload()
        return _json(login(data.get("username"), data.get("password")))

    @app.route("/new_email", methods=["PUT"])
    def new_email():
        data = _payload()
        return _json(update_email(data.get("username"), data.get("email")))

    @app.route("/del_account", methods=["DELETE"])
    def del_account():
        data = _payload()
        return _json(delete_account(data.get("username")))

    @app.route("/profile", methods=["GET", "POST", "PUT"])
    def profile():
        data = _payload()
        if request.method == "GET":
            return _json(get_bio_data(data.get("username")))
        return _json(
            add_bio_data(
                data.get("username"),
                data.get("gender"),
                data.get("height"),
                data.get("weight"),
                data.get("body_fat"),
                data.get("age"),
                data.get("activity"),
            )
        )

    @app.route("/preferences", methods=["GET"])
    def preferences():
        data = _payload()
        return _json(get_preferences(data.get("username")))

    @app.route("/preferences/diet", methods=["POST", "DELETE"])
    def preference_diet():
        data = _payload()
        if request.method == "POST":
            return _json(add_restriction(data.get("username"), data.get("restriction")))
        return _json(remove_restriction(data.get("username"), data.get("restriction")))

    @app.route("/preferences/sensitivity", methods=["POST", "PUT", "DELETE"])
    def preference_sensitivity():
        data = _payload()
        if request.method == "POST":
            return _json(add_allergen(data.get("username"), data.get("allergen"), data.get("severity")))
        if request.method == "PUT":
            return _json(update_allergen_severity(data.get("username"), data.get("allergen"), data.get("severity")))
        return _json(remove_allergen(data.get("username"), data.get("allergen")))

    @app.route("/search", methods=["GET", "POST"])
    def search():
        data = _payload()
        return _json(_search_response(data.get("query"), data.get("username")))

    @app.route("/meals", methods=["GET", "POST", "PUT", "DELETE"])
    def meals():
        data = _payload()
        if request.method == "GET":
            return _json(get_meals(data.get("username")))
        if request.method == "POST":
            return _json(add_meal(data.get("username"), data.get("recipe_id"), data.get("eaten_at")))
        if request.method == "PUT":
            if data.get("recipe_id_new"):
                return _json(update_meal(data.get("username"), data.get("user_meal_id"), data.get("recipe_id_new")))
            return _json(update_meal_time(data.get("username"), data.get("user_meal_id"), data.get("eaten_at")))
        return _json(
            remove_meal(
                data.get("username"),
                user_meal_id=data.get("user_meal_id"),
                recipe_id=data.get("recipe_id"),
                eaten_at=data.get("eaten_at"),
            )
        )

    @app.route("/goals", methods=["GET", "POST", "PUT", "DELETE"])
    def goals():
        data = _payload()
        if request.method == "GET":
            return _json(get_goals(data.get("username")))
        if request.method == "POST":
            return _json(add_goal(data.get("username"), data.get("nutrient"), data.get("amount"), data.get("min_max")))
        if request.method == "PUT":
            return _json(update_goal(data.get("username"), data.get("nutrient"), data.get("amount"), data.get("min_max")))
        return _json(remove_goal(data.get("username"), data.get("nutrient")))

    @app.route("/progress", methods=["GET"])
    def progress():
        data = _payload()
        period = data.get("period", "daily")
        if period == "weekly":
            return _json(weekly_nutrient_progress(data.get("username")))
        return _json(daily_nutrient_progress(data.get("username")))

    @app.route("/recommendations", methods=["GET", "POST"])
    def recommendations():
        data = _payload()
        if request.method == "POST" and data.get("action"):
            return _json(save_recommendation_feedback(data.get("username"), data.get("recipe_id"), data.get("action")))
        return _json(get_recommendations(data.get("username"), data.get("query")))

    @app.route("/recommended-goals", methods=["GET"])
    def recommended_goals():
        data = _payload()
        return _json(recommended_goal(data.get("username")))

    @app.route("/chat", methods=["POST"])
    def chat():
        data = _payload()
        return _json(
            chat_with_model(
                data.get("username"),
                data.get("message"),
                history=data.get("history") or [],
                recommendations=data.get("recommendations") or [],
            )
        )

    def legacy_weekly_progress():
        data = _payload()
        return _json(weekly_nutrient_progress(data.get("username")))

    def legacy_daily_progress():
        data = _payload()
        return _json(daily_nutrient_progress(data.get("username")))

    # Legacy route aliases used by the original prototype and tests.
    app.add_url_rule("/get_usr_meals", "get_usr_meals", meals, methods=["GET"])
    app.add_url_rule("/add_usr_meal", "add_usr_meal", meals, methods=["POST"])
    app.add_url_rule("/del_usr_meal", "del_usr_meal", meals, methods=["DELETE"])
    app.add_url_rule("/update_usr_meal", "update_usr_meal", meals, methods=["PUT"])
    app.add_url_rule("/update_usr_meal_time", "update_usr_meal_time", meals, methods=["PUT"])
    app.add_url_rule("/get_usr_goals", "get_usr_goals", goals, methods=["GET"])
    app.add_url_rule("/add_usr_goal", "add_usr_goal", goals, methods=["POST"])
    app.add_url_rule("/update_usr_goal", "update_usr_goal", goals, methods=["PUT"])
    app.add_url_rule("/del_usr_goal", "del_usr_goal", goals, methods=["DELETE"])
    app.add_url_rule("/add_allergy", "add_allergy", preference_sensitivity, methods=["POST"])
    app.add_url_rule("/del_allergy", "del_allergy", preference_sensitivity, methods=["DELETE"])
    app.add_url_rule("/update_severity", "update_severity", preference_sensitivity, methods=["PUT"])
    app.add_url_rule("/add_diet", "add_diet", preference_diet, methods=["POST"])
    app.add_url_rule("/del_diet", "del_diet", preference_diet, methods=["DELETE"])
    app.add_url_rule("/add_bio", "add_bio", profile, methods=["POST"])
    app.add_url_rule("/usr_weekly_nutrient_progress", "usr_weekly_nutrient_progress", legacy_weekly_progress, methods=["GET"])
    app.add_url_rule("/usr_daily_nutrient_progress", "usr_daily_nutrient_progress", legacy_daily_progress, methods=["GET"])
    app.add_url_rule("/rec_goal", "rec_goal", recommended_goals, methods=["GET"])

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True, host="127.0.0.1", port=5000)
