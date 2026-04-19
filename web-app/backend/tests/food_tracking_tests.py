#The purpose of this file is to test the functions in food_tracking.py

from food_tracking import *
from main import create_app

"""
THIS IS A LEGACY TEST FROM BEFORE INCLUDING API CALLS
"""
"""
def test_valid_meal_ops():
    app = create_app()
    with app.app_context():
        #Add a meal for the user
        res = add_meal("NOTTAKEN","scrambled eggs","1999-12-31 11:59:59")
        assert('success' in res['message'] and res['id'] is not None)
        meal_id = res['id']
        #Check that the meal is in the database
        res = get_meals("NOTTAKEN")
        assert(res['success'] and res['data'] is not None)
        assert(meal_id in res['data'][0] and "scrambled eggs" in res['data'][0])
        #Update the meal
        res = update_meal(meal_id,"scrambled eggs and bacon","2000-01-01 12:00:00")
        assert('success' in res)
        #Check that the change is reflected in the database
        res = get_meals("NOTTAKEN")
        assert(res['success'] and res['data'] is not None)
        assert("scrambled eggs and bacon" in res['data'][0] and meal_id in res['data'][0])
        #Remove the meal
        res = remove_meal(meal_id)
        assert('success' in res)
        #Check that the meal has been removed in the database
        res = get_meals("NOTTAKEN")
        assert(res['success'] and len(res['data'])==0)
"""

def test_query_build():
    app = create_app()

def test_meal_search():
    app = create_app()