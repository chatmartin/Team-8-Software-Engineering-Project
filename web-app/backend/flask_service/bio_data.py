#The purpose of this function is to allow the user to include their biometric data

from globals import *

def add_bio_data(username,gender,height,weight,body_fat,age):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "INSERT INTO user_bio_data(user_id,gender,height,weight,body_fat,age) VALUES (%s,%s,%s,%s,%s,%s)"
        cursor.execute(query,(user_id,gender,height,weight,body_fat,age))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Data insertion unsuccessful."
        return "Data inserted successfully."

def update_gender(username,gender):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "UPDATE user_bio_data SET gender=%s WHERE user_id=%s"
        cursor.execute(query, (gender,user_id))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Gender update unsuccessful."
        return "Gender updated successfully."

def update_height(username,height):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "UPDATE user_bio_data SET height=%s WHERE user_id=%s"
        cursor.execute(query, (height,user_id))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Height update unsuccessful."
        return "Height updated successfully."

def update_weight(username,weight):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "UPDATE user_bio_data SET weight=%s WHERE user_id=%s"
        cursor.execute(query, (weight,user_id))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Weight update unsuccessful."
        return "Weight updated successfully."

def update_body_fat(username,body_fat):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "UPDATE user_bio_data SET body_fat=%s WHERE user_id=%s"
        cursor.execute(query, (body_fat,user_id))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Body fat percentage update unsuccessful."
        return "Body fat percentage updated successfully."

def update_age(username,age):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Could not connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found."
        user_id = row[0]
        query = "UPDATE user_bio_data SET age=%s WHERE user_id=%s"
        cursor.execute(query, (age,user_id))
        conn.commit()
        if conn.rowcount == 0:
            return "ERROR: Age update unsuccessful."
        return "Age updated successfully."