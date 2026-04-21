"""Recommended nutrition goals from basic profile data."""

from .globals import fail, get_db_conn, ok


def recommended_goal(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM login_info WHERE username=%s", (username,))
        row = cursor.fetchone()
        if row is None:
            return fail("User not found.", 404)
        user_id = row[0]
        cursor.execute(
            """
            SELECT gender, height, weight, body_fat, age, activity_level
            FROM user_bio_data
            WHERE user_id=%s
            """,
            (user_id,),
        )
        row = cursor.fetchone()

    if row is None:
        weight = 70
        height = 170
        age = 40
        gender = "male"
        body_fat = 25
        activity = 1.2
    else:
        gender = row[0] or "male"
        height = float(row[1] or 67) * 2.54
        weight = float(row[2] or 154) * 0.453592
        body_fat = float(row[3] or 25)
        age = int(row[4] or 40)
        activity = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
        }.get(row[5], 1.2)

    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    lean_mass = weight * (1 - body_fat / 100)
    tdee = (bmr + 370 + 21.6 * lean_mass) * activity
    nutrients = {
        "calories": round(tdee),
        "protein": round((tdee * 0.25) / 4, 1),
        "fat": round((tdee * 0.3) / 9, 1),
        "carbohydrates": round((tdee * 0.45) / 4, 1),
        "saturated fat": round((tdee * 0.1) / 9, 1),
        "sugar": round((tdee * 0.1) / 4, 1),
        "alcohol": 0,
        "fiber": 25 if gender == "female" else 38,
        "copper": 0.9,
        "calcium": 1.3,
        "sodium": 2300,
        "choline": 550,
        "cholesterol": 300,
        "folate": 400,
        "iodine": 150,
        "iron": 18,
        "magnesium": 420,
        "manganese": 2.3,
        "phosphorus": 1250,
        "potassium": 4700,
        "selenium": 55,
        "vitamin a": 900,
        "vitamin b5": 5,
        "vitamin b6": 1.7,
        "vitamin b12": 2.4,
        "vitamin c": 90,
        "vitamin d": 20,
        "vitamin e": 15,
        "vitamin k": 120,
        "zinc": 11,
    }
    if gender == "female":
        nutrients.update({"vitamin b1": 1.1, "vitamin b2": 1.1, "vitamin b3": 14})
    else:
        nutrients.update({"vitamin b1": 1.2, "vitamin b2": 1.3, "vitamin b3": 16})
    return ok("Recommended goals calculated successfully.", nutrients)
