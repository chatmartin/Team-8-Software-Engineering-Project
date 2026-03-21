#The purpose of this file is to manage the food tracking capability
#Spoonacular API key found in globals.py

from globals import *

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
        query = "SELECT * FROM meals WHERE meal_id IN (SELECT meal_id FROM user_meals WHERE user_id = %s"
        cursor.execute(query, (row[0],))
        return {"success":True,"data":cursor.fetchall()}

#TODO: May need to modify eaten_at depending on how we take it in as input
#TODO: Make sure the food is actually in the spoonacular API
def add_meal(username,meal,eaten_at):
    conn = get_db_conn()
    if conn is None:  # if database is not connected, give an error
        return {"message":"ERROR: Unable to access database.","id":None}
    with conn.cursor() as cursor:
        #First make sure the user exists and get their user id if they do. If they don't exist, return an error
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query,(username,))
        row = cursor.fetchone()
        if row is None:
            return {"message":"ERROR: User not found.","id":None}
        uid = row[0]
        #Second, insert the meal into the meal table
        query = "INSERT INTO meals (meal,eaten_at) VALUES (%s,%s)"
        cursor.execute(query,(meal,eaten_at,))
        conn.commit()
        #Third, get the generated meal id
        query = "SELECT meal_id FROM meals WHERE meal = %s AND eaten_at = %s"
        cursor.execute(query,(meal,eaten_at,))
        row = cursor.fetchone()
        meal_id = row[0]
        #Finally, connect the meal to its corresponding user
        query = "INSERT INTO user_meals (user_id, meal_id) VALUES (%s,%s)"
        cursor.execute(query,(uid,meal_id,))
        conn.commit()
        return {"message":"Meal added successfully.","id":meal_id}

#Allows the user to remove an existing meal
def remove_meal(meal_id):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT * FROM meals WHERE meal_id = %s"
        cursor.execute(query,(meal_id,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        #Remove the meal from the meals table and from the user meal table
        query = "DELETE FROM meals WHERE meal_id = %s"
        cursor.execute(query,(meal_id,))
        conn.commit()
        query = "DELETE FROM user_meals WHERE meal_id = %s"
        cursor.execute(query,(meal_id,))
        return "Meal removed successfully."

#Allows the user to update an existing meal. Note that we only need to change the meal table since the particular meal is still connected to the same user
def update_meal(meal_id,meal,eaten_at):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        #Now, update the data
        query = "UPDATE meals SET meal=%s, eaten_at=%s WHERE meal_id=%s"
        cursor.execute(query,(meal,eaten_at,meal_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Meal not found."
        return "Meal updated successfully."

