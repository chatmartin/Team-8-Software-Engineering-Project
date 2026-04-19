#The purpose of this file is to allow users to add allergens/dislikes as well as dietary restrictions
#The idea is that on the frontend, they have a restricted selection of allergens they can input as low/high severity
#They can also input ingredients they don't like with low/high levels of dislike (no restrictions)
#This also helps with tracking dietary restrictions, as they can choose from a selection of diets

from globals import *

#Since adding/deleting/updating an allergen vs dislike has very similar logic, they will use the same functions
def add_allergen(username,allergen,severity):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to connect to the database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found"
        user_id = row[0]
        query = "SELECT ingredient_id FROM ingredients WHERE ingredient=%s"
        cursor.execute(query, (allergen,))
        row = cursor.fetchone()
        if row is None:
            if severity == 'high':
                return "ERROR: Allergen not found"
            query = "INSERT INTO ingredients(ingredient) VALUES(%s)"
            cursor.execute(query, (allergen,))
            query = "SELECT ingredient_id FROM ingredients WHERE ingredient=%s"
            cursor.execute(query, (allergen,))
            row = cursor.fetchone()
        ingredient_id = row[0]
        query = "INSERT INTO user_allergies(user_id,severity,allergen_id) VALUES(%s,%s,%s)"
        cursor.execute(query, (user_id, severity, ingredient_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Allergen insertion unsuccessful" #Shouldn't happen, but this is a safety measure
        return "Allergen added successfully"

def add_restriction(username,restriction):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found"
        user_id = row[0]
        query = "SELECT restriction_id FROM dietary_restrictions WHERE restriction=%s"
        cursor.execute(query, (restriction,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Restriction not found" #Shouldn't happen, this is a safety measure
        restriction_id = row[0]
        query = "INSERT INTO user_restrictions(user_id,restriction_id) VALUES(%s,%s)"
        cursor.execute(query, (user_id, restriction_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Restriction insertion unsuccessful"
        return "Restriction added successfully"


def remove_allergen(username,allergen):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found"
        user_id = row[0]
        query = "SELECT ingredient_id FROM ingredients WHERE ingredient=%s"
        cursor.execute(query, (allergen,))
        ingredient_id = cursor.fetchone()[0]
        query = "DELETE FROM user_allergies WHERE user_id=%s AND allergen_id=%s"
        cursor.execute(query, (user_id, ingredient_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Allergen deletion unsuccessful"
        return "Allergen removed successfully"

def remove_restriction(username,restriction):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found"
        user_id = row[0]
        query = "SELECT restriction_id FROM dietary_restrictions WHERE restriction=%s"
        cursor.execute(query, (restriction,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Restriction not found"
        restriction_id = row[0]
        query = "DELETE FROM user_restrictions WHERE user_id=%s AND restriction_id=%s"
        cursor.execute(query, (user_id, restriction_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Restriction deletion unsuccessful"


def update_allergen_severity(username,allergen,new_severity):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: User not found"
        user_id = row[0]
        query = "SELECT ingredient_id FROM ingredients WHERE ingredient=%s"
        cursor.execute(query, (allergen,))
        row = cursor.fetchone()
        if row is None:
            return "ERROR: Ingredient not found"
        ingredient_id = row[0]
        query = "UPDATE user_allergies SET severity=%s WHERE user_id=%s AND allergen_id=%s"
        cursor.execute(query, (new_severity, user_id, ingredient_id))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: Severity update unsuccessful"
        return "Severity updated successfully"
