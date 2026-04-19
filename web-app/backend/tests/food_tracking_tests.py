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
    with app.app_context():
        conn = get_db_conn()
        with conn.cursor() as cursor:
            query_list = query_builder('Pasta Alfredo', 'NOTTAKEN',cursor)
            assert(query_list[0]=='pasta alfredo')
            assert('ketogenic' in query_list[1] and len(query_list[1])==1)
            assert('tree nut' in query_list[2] and len(query_list[2])==1)
            assert('shellfish' in query_list[3] and 'pork' in query_list[3] and 'alcohol' in query_list[3] and 'blood' in query_list[3] and len(query_list[3])==4)



def test_meal_search_restrictive():
    app = create_app()
    with app.app_context():
        app = create_app()
        with app.app_context():
            results = search_meal('Caesar Salad', 'NOTTAKEN')
            meal_data = results[0]
            meal = meal_data['meal']
            recipe_id = meal_data['recipe_id']
            ingredients = meal_data['ingredients']
            nutrients = meal_data['nutrients']
            conn = get_db_conn()
            with conn.cursor() as cursor:
                query = "SELECT meal,meal_id FROM meals WHERE recipe_id = %s"
                cursor.execute(query, (recipe_id,))
                row = cursor.fetchone()
                assert (row is not None)
                assert (row[0] == meal)
                meal_id = row[1]
                query = "SELECT ingredient FROM meal_ingredients m JOIN ingredients i ON m.ingredient_id = i.ingredient_id WHERE m.meal_id = %s"
                cursor.execute(query, (meal_id,))
                rows = cursor.fetchall()
                assert (rows is not None)
                for ingredient in ingredients:
                    formatted = (ingredient['name'],)
                    assert (formatted in rows)
                query = "SELECT name FROM meal_nutrients m JOIN nutrients n ON m.nutrient_id = n.nutrient_id WHERE m.meal_id = %s"
                cursor.execute(query, (meal_id,))
                rows = cursor.fetchall()
                assert (rows is not None)


def test_meal_search_no_restrictions():
    app = create_app()
    with app.app_context():
        app = create_app()
        with app.app_context():
            results = search_meal('Pasta Alfredo', 'test')
            meal_data = results[0]
            meal = meal_data['meal']
            recipe_id = meal_data['recipe_id']
            ingredients = meal_data['ingredients']
            nutrients = meal_data['nutrients']
            conn = get_db_conn()
            with conn.cursor() as cursor:
                query = "SELECT meal,meal_id FROM meals WHERE recipe_id = %s"
                cursor.execute(query, (recipe_id,))
                row = cursor.fetchone()
                assert (row is not None)
                assert (row[0] == meal)
                meal_id = row[1]
                query = "SELECT ingredient FROM meal_ingredients m JOIN ingredients i ON m.ingredient_id = i.ingredient_id WHERE m.meal_id = %s"
                cursor.execute(query, (meal_id,))
                rows = cursor.fetchall()
                assert (rows is not None)
                for ingredient in ingredients:
                    formatted = (ingredient['name'],)
                    assert (formatted in rows)
                query = "SELECT name FROM meal_nutrients m JOIN nutrients n ON m.nutrient_id = n.nutrient_id WHERE m.meal_id = %s"
                cursor.execute(query, (meal_id,))
                rows = cursor.fetchall()
                assert (rows is not None)

def test_meal_search_no_results():
    app = create_app()
    with app.app_context():
        results = search_meal('Pasta Alfredo', 'NOTTAKEN')
        assert(len(results)==0)