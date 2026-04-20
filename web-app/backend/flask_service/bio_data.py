"""User biometric/profile data."""

from .globals import fail, get_db_conn, ok


PROFILE_FIELDS = {
    "gender": "gender",
    "height": "height",
    "weight": "weight",
    "body_fat": "body_fat",
    "age": "age",
    "activity": "activity_level",
}


def _user_id(cursor, username):
    cursor.execute("SELECT user_id FROM login_info WHERE username=%s", (username,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_bio_data(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT gender, height, weight, body_fat, age, activity_level
            FROM user_bio_data
            WHERE user_id=%s
            """,
            (uid,),
        )
        row = cursor.fetchone()
        if row is None:
            return ok("Profile has not been completed.", {"onboarding_complete": False})
        return ok(
            "Profile obtained successfully.",
            {
                "onboarding_complete": True,
                "gender": row[0],
                "height": row[1],
                "weight": row[2],
                "body_fat": row[3],
                "age": row[4],
                "activity": row[5],
            },
        )


def add_bio_data(username, gender, height, weight, body_fat, age, activity):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            INSERT INTO user_bio_data(user_id, gender, height, weight, body_fat, age, activity_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                gender = EXCLUDED.gender,
                height = EXCLUDED.height,
                weight = EXCLUDED.weight,
                body_fat = EXCLUDED.body_fat,
                age = EXCLUDED.age,
                activity_level = EXCLUDED.activity_level
            """,
            (uid, gender, height, weight, body_fat, age, activity),
        )
        conn.commit()
        return ok(
            "Profile saved successfully.",
            {
                "onboarding_complete": True,
                "gender": gender,
                "height": height,
                "weight": weight,
                "body_fat": body_fat,
                "age": age,
                "activity": activity,
            },
        )


def _update_profile_field(username, field, value):
    column = PROFILE_FIELDS[field]
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(f"UPDATE user_bio_data SET {column}=%s WHERE user_id=%s", (value, uid))
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Profile not found.", 404)
        return ok("Profile updated successfully.", {field: value})


def update_gender(username, gender):
    return _update_profile_field(username, "gender", gender)


def update_height(username, height):
    return _update_profile_field(username, "height", height)


def update_weight(username, weight):
    return _update_profile_field(username, "weight", weight)


def update_body_fat(username, body_fat):
    return _update_profile_field(username, "body_fat", body_fat)


def update_age(username, age):
    return _update_profile_field(username, "age", age)


def update_activity(username, activity):
    return _update_profile_field(username, "activity", activity)
