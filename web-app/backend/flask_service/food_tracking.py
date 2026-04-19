from .globals import get_db_conn


def get_meals(username):
    conn = get_db_conn()
    if conn is None:
        return {"success": False, "message": "ERROR: Unable to access database."}
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return {"success": False, "message": "ERROR: User not found."}
        query = "SELECT * FROM meals WHERE meal_id IN (SELECT meal_id FROM user_meals WHERE user_id = %s)"
        cursor.execute(query, (row[0],))
        return {"success": True, "data": cursor.fetchall()}


def add_meal(username, meal, eaten_at):
    conn = get_db_conn()
    if conn is None:
        return {"message": "ERROR: Unable to access database.", "id": None}
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return {"message": "ERROR: User not found.", "id": None}
        uid = row[0]
        query = "INSERT INTO meals (meal,eaten_at) VALUES (%s,%s)"
        cursor.execute(query, (meal, eaten_at))
        conn.commit()
        query = "SELECT meal_id FROM meals WHERE meal = %s AND eaten_at = %s"
        cursor.execute(query, (meal, eaten_at))
        row = cursor.fetchone()
        meal_id = row[0]
        query = "INSERT INTO user_meals (user_id, meal_id) VALUES (%s,%s)"
        cursor.execute(query, (uid, meal_id))
        conn.commit()
        return {"message": "Meal added successfully.", "id": meal_id}


def remove_meal(meal_id):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT * FROM meals WHERE meal_id = %s"
        cursor.execute(query, (meal_id,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Meal not found."
        query = "DELETE FROM meals WHERE meal_id = %s"
        cursor.execute(query, (meal_id,))
        conn.commit()
        return "Meal removed successfully."


def update_meal(meal_id, meal, eaten_at):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "UPDATE meals SET meal=%s, eaten_at=%s WHERE meal_id=%s"
        cursor.execute(query, (meal, eaten_at, meal_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Meal not found."
        return "Meal updated successfully."
