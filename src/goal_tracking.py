#The purpose of this file is for storing data related to dietary/nutritional goals

from globals import *

def get_goals(username):
    conn = get_db_conn()
    if conn is None:
        return {"message":"ERROR: Unable to access database.","goals":None}
    with conn.cursor() as cursor:
        #Step 1: Get user ID
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        #Make sure user exists
        if row is None:
            return {"message":"ERROR: Username does not exist.","goals":None}
        uid = row[0]
        #Step 2: Get all goals and their data
        query = "SELECT n.name,ug.target_amount,n.unit,ug.min_max FROM user_goals ug JOIN nutrients n ON ug.nutrient_id=n.nutrient_id WHERE ug.user_id=%s"
        cursor.execute(query, (uid,))
        rows = cursor.fetchall()
        goals = [
            {
                "nutrient":row[0],
                "target":row[1],
                "unit":row[2],
                "min_max":row[3]
            }
            for row in rows
        ]
        return {"message":"Goals obtained successfully.","goals":goals}

def add_goal(username,nutrient,amount,min_max):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        #Step 1: Get user ID
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query, (username,))
        # Make sure user exists
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        uid = row[0]
        #Step 2: Get nutrient ID
        query = "SELECT nutrient_id FROM nutrient WHERE name = %s"
        cursor.execute(query, (nutrient,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Nutrient not found."
        nid = row[0]
        #Step 3: Add goal into database
        query = "INSERT INTO user_goals(user_id,nutrient_id,target_amount,min_max) VALUES (%s,%s,%s,%s)"
        cursor.execute(query, (uid,nid,amount,min_max))
        conn.commit()
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Goal not found."
        return "Goal added successfully."

def update_goal(username,nutrient,amount,min_max):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        uid = row[0]
        query = "SELECT nutrient_id FROM nutrient WHERE name = %s"
        cursor.execute(query, (nutrient,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Nutrient not found."
        nid = row[0]
        query = "UPDATE user_goals SET target_amount = %s,min_max = %s WHERE user_id = %s AND nutrient_id = %s"
        cursor.execute(query, (amount,min_max,uid,nid))
        conn.commit()
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Goal not found."
        return "Goal updated successfully."

def remove_goal(username,nutrient):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        uid = row[0]
        query = "SELECT nutrient_id FROM nutrient WHERE name = %s"
        cursor.execute(query, (nutrient,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Nutrient not found."
        nid = row[0]
        query = "DELETE FROM user_goals WHERE user_id = %s AND nutrient_id = %s"
        cursor.execute(query, (uid,nid))
        conn.commit()
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Goal not found."
        return "Goal removed successfully."