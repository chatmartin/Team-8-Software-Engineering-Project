#The purpose of this file is to manage the food tracking capability
#Spoonacular API key found in globals.py

from spoonacular_api_calls import *

def query_builder(meal_query,username,cursor):
    # Take care of allergens and strong dislikes
    query = "SELECT ingredient,severity FROM (ingredients i JOIN user_allergies a ON allergen_id = ingredient_id) JOIN login_info l ON a.user_id = l.user_id WHERE username = %s AND (severity = 'high' OR severity = 'medium')"
    cursor.execute(query, (username,))
    rows = cursor.fetchall()
    allergens = []
    excludes = []
    for risk in rows:
        if risk[1] == 'high':
            allergens.append(risk[0])
        else:
            excludes.append(risk[0])

    # Account for user diet
    query = "SELECT restriction FROM (user_restrictions u JOIN dietary_restrictions r ON u.restriction_id = r.restriction_id) JOIN login_info l ON u.user_id = l.user_id WHERE username = %s"
    cursor.execute(query, (username,))
    rows = cursor.fetchall()
    diets = []
    for diet in rows:
        if diet[0] in valid_diets:
            diets.append(diet[0])
        else:
            if (diet[0] == 'halal' or diet[0] == 'kosher') and 'pork' not in excludes:
                excludes.append('pork')
            if diet[0] == 'halal':
                if 'alcohol' not in excludes:
                    excludes.append('alcohol')
                if 'blood' not in excludes:
                    excludes.append('blood')
            if diet[0] == 'kosher':
                if 'shellfish' not in excludes:
                    excludes.append('shellfish')
                if 'squid' not in excludes:
                    excludes.append('squid')
                if 'octopus' not in excludes:
                    excludes.append('octopus')
                if 'shark' not in excludes:
                    excludes.append('shark')
                if 'eel' not in excludes:
                    excludes.append('eel')
                if 'insects' not in excludes:
                    excludes.append('insects')
                if 'blood' not in excludes:
                    excludes.append('blood')
                if 'rabbit' not in excludes:
                    excludes.append('rabbit')
                if 'camel' not in excludes:
                    excludes.append('camel')
            if diet[0] == 'beef free' and 'beef' not in excludes:
                excludes.append('beef')
            if diet[0] == 'dairy free' and 'dairy' not in excludes:
                excludes.append('dairy')
            if diet[0] == 'egg free' and 'egg' not in excludes:
                excludes.append('egg')
    query_list = [meal_query.lower(), sorted(diets), sorted(allergens), sorted(excludes)]
    return query_list

def cache_results(query_list,signature,cursor,conn):
    # insert query
    cursor.execute(
        "INSERT INTO queries (query_signature) VALUES (%s)",
        (signature,)
    )
    conn.commit()

    # get query id
    cursor.execute(
        "SELECT query_id FROM queries WHERE query_signature = %s",
        (signature,)
    )
    qid = cursor.fetchone()[0]

    # call API
    meal_results = fetch_meals(query_list[0], query_list[1], query_list[2], query_list[3])
    if not meal_results:
        return False

    # loop through meals with rank
    for rank, meal in enumerate(meal_results, start=1):

        # STEP 2A: Check if meal exists
        cursor.execute(
            "SELECT meal_id FROM meals WHERE recipe_id = %s",
            (meal['recipe_id'],)
        )
        row = cursor.fetchone()

        if row is None:
            # insert meal
            cursor.execute(
                "INSERT INTO meals (meal, recipe_id) VALUES (%s, %s)",
                (meal['meal'], meal['recipe_id'])
            )
            conn.commit()

            # get meal id
            cursor.execute(
                "SELECT meal_id FROM meals WHERE recipe_id = %s",
                (meal['recipe_id'],)
            )
            mid = cursor.fetchone()[0]

            # Insert nutrients
            for nutrient, val in meal['nutrients'].items():
                cursor.execute(
                    "SELECT nutrient_id FROM nutrients WHERE name = %s",
                    (nutrient,)
                )
                nrow = cursor.fetchone()
                if nrow is None:
                    continue  # skip if not found (extra safety measure, shouldn't happen)

                nid = nrow[0]

                cursor.execute(
                    "INSERT INTO meal_nutrients (meal_id, nutrient_id, amount) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (mid, nid, val['amount'])
                )
                conn.commit()

            # Insert ingredients
            for ing in meal['ingredients']:

                cursor.execute(
                    "SELECT ingredient_id FROM ingredients WHERE ingredient = %s",
                    (ing['name'],)
                )
                irow = cursor.fetchone()

                if irow is None:
                    cursor.execute(
                        "INSERT INTO ingredients (ingredient) VALUES (%s)",
                        (ing['name'],)
                    )
                    conn.commit()

                    cursor.execute(
                        "SELECT ingredient_id FROM ingredients WHERE ingredient = %s",
                        (ing['name'],)
                    )
                    iid = cursor.fetchone()[0]
                else:
                    iid = irow[0]

                cursor.execute(
                    "INSERT INTO meal_ingredients (meal_id, ingredient_id, amount, unit) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (mid, iid, ing['amount'], ing['unit'])
                )
                conn.commit()

            conn.commit()

        else:
            mid = row[0]

        # Insert rank
        cursor.execute(
            "INSERT INTO meal_queries (meal_id, query_id, rank) VALUES (%s, %s, %s)",
            (mid, qid, rank)
        )

    conn.commit()
    return True

#TODO: May need to modify
def search_meal(meal_query, username):
    conn = get_db_conn()
    if conn is None:
        return None

    with conn.cursor() as cursor:
        # STEP 0: build the query signature
        query_list = query_builder(meal_query, username, cursor)
        signature = f"{query_list[0]}|{','.join(query_list[1])}|{','.join(query_list[2])}|{','.join(query_list[3])}"

        # STEP 1: check if query exists
        cursor.execute(
            "SELECT query_id FROM queries WHERE query_signature = %s",
            (signature,)
        )
        row = cursor.fetchone()

        # STEP 2: if not cached then fetch and store
        if row is None:
            if not cache_results(query_list,signature,cursor,conn):
                return None


        # STEP 3: fetch cached results
        cursor.execute(
            """
            SELECT m.meal_id, m.meal, m.recipe_id
            FROM meal_queries mq
            JOIN queries q ON mq.query_id = q.query_id
            JOIN meals m ON mq.meal_id = m.meal_id
            WHERE q.query_signature = %s
            ORDER BY mq.rank
            """,
            (signature,)
        )

        rows = cursor.fetchall()
        meal_results = []

        for row in rows:
            mid, meal_name, recipe_id = row

            meal_data = {
                "meal": meal_name,
                "recipe_id": recipe_id,
                "ingredients": [],
                "nutrients": {},
            }

            # ingredients
            cursor.execute(
                """
                SELECT i.ingredient, m.amount, m.unit
                FROM meal_ingredients m
                JOIN ingredients i ON m.ingredient_id = i.ingredient_id
                WHERE m.meal_id = %s
                """,
                (mid,)
            )

            for ing in cursor.fetchall():
                meal_data["ingredients"].append({
                    "name": ing[0],
                    "amount": ing[1],
                    "unit": ing[2]
                })

            # nutrients
            cursor.execute(
                """
                SELECT n.name, m.amount
                FROM meal_nutrients m
                JOIN nutrients n ON m.nutrient_id = n.nutrient_id
                WHERE m.meal_id = %s
                """,
                (mid,)
            )

            for nut in cursor.fetchall():
                meal_data["nutrients"][nut[0]] = nut[1]


            meal_results.append(meal_data)

        return meal_results




def get_meals(username):
    conn = get_db_conn()
    if conn is None: #if database is not connected, give an error
        return {"success":False,"message":"ERROR: Unable to access database."}
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return {"success": False, "message": "ERROR: User not found."}
        query = "SELECT m.meal_id,meal,recipe_id,eaten_at FROM meals m JOIN user_meals u ON m.meal_id = u.meal_id WHERE user_id = %s"
        cursor.execute(query, (row[0],))
        return {"success":True,"data":cursor.fetchall()}

#TODO: May need to modify eaten_at depending on how we take it in as input
def add_meal(username,recipe_id,eaten_at):
    conn = get_db_conn()
    if conn is None:  # if database is not connected, give an error
        return {"message":"ERROR: Unable to access database.","id":None}
    with conn.cursor() as cursor:
        #First, make sure the user exists and get their user id if they do. If they don't exist, return an error
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return {"message":"ERROR: User not found.","id":None}
        uid = row[0]
        #Second, get the meal id
        query = "SELECT meal_id FROM meals WHERE recipe_id = %s"
        cursor.execute(query,(recipe_id,))
        meal_id = cursor.fetchone()[0]
        #Third, insert the meal into the user meals table
        query = "INSERT INTO user_meals (user_id, meal_id, eaten_at) VALUES (%s,%s,%s)"
        cursor.execute(query,(uid,meal_id,eaten_at))
        conn.commit()
        return {"message":"Meal added successfully.","id":meal_id}

#Allows the user to remove an existing meal
def remove_meal(username,recipe_id,eaten_at):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT meal_id FROM meals WHERE recipe_id = %s"
        cursor.execute(query,(recipe_id,))
        meal_id = cursor.fetchone()[0]
        query = "SELECT * FROM meals WHERE meal_id = %s"
        cursor.execute(query,(meal_id,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        #Remove the meal from the user_meals table
        query = "DELETE FROM user_meals WHERE meal_id = %s AND user_id = %s AND eaten_at = %s"
        cursor.execute(query,(meal_id,row[0],eaten_at))
        conn.commit()
        return "Meal removed successfully."

#Allows the user to update when a meal was eaten
def update_meal_time(username,recipe_id,eaten_at):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        #get the user id
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        #get the meal id
        query = "SELECT meal_id FROM meals WHERE recipe_id = %s"
        cursor.execute(query,(recipe_id,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        meal_id = row[0]
        #Now, update the data
        query = "UPDATE user_meals SET eaten_at=%s WHERE meal_id=%s,user_id=%s"
        cursor.execute(query,(eaten_at,meal_id,user_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Meal not found."
        return "Meal updated successfully."

def update_meal(username,old_recipe_id,new_recipe_id):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "SELECT meal_id FROM meals WHERE recipe_id = %s"
        cursor.execute(query,(new_recipe_id,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        new_meal_id = row[0]
        query = "SELECT m.meal_id FROM meals m JOIN user_meals u ON m.meal_id = u.meal_id WHERE user_id = %s AND recipe_id = %s"
        cursor.execute(query,(user_id,old_recipe_id))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        old_meal_id = row[0]
        query = "UPDATE user_meals SET meal_id=%s WHERE meal_id=%s"
        cursor.execute(query,(new_meal_id,old_meal_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Meal not found."
        return "Meal updated successfully."