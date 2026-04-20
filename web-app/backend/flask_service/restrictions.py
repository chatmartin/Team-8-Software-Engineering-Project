"""Dietary restrictions, allergens, and dislike preferences."""

from .globals import fail, get_db_conn, ok


def _user_id(cursor, username):
    cursor.execute("SELECT user_id FROM login_info WHERE username=%s", (username,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_preferences(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT i.ingredient, ua.severity
            FROM user_allergies ua
            JOIN ingredients i ON i.ingredient_id = ua.allergen_id
            WHERE ua.user_id = %s
            ORDER BY ua.severity, i.ingredient
            """,
            (uid,),
        )
        sensitivities = [
            {"ingredient": row[0], "severity": row[1]} for row in cursor.fetchall()
        ]
        cursor.execute(
            """
            SELECT dr.restriction
            FROM user_restrictions ur
            JOIN dietary_restrictions dr ON dr.restriction_id = ur.restriction_id
            WHERE ur.user_id = %s
            ORDER BY dr.restriction
            """,
            (uid,),
        )
        diets = [row[0] for row in cursor.fetchall()]
        return ok("Preferences obtained successfully.", {"diets": diets, "sensitivities": sensitivities})


def add_allergen(username, allergen, severity):
    if severity not in {"low", "medium", "high"}:
        return fail("Severity must be low, medium, or high.")
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    ingredient = (allergen or "").strip().lower()
    if not ingredient:
        return fail("Ingredient is required.")
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient=%s", (ingredient,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO ingredients(ingredient) VALUES(%s) RETURNING ingredient_id", (ingredient,))
            ingredient_id = cursor.fetchone()[0]
        else:
            ingredient_id = row[0]
        cursor.execute(
            """
            INSERT INTO user_allergies(user_id, severity, allergen_id)
            VALUES(%s, %s, %s)
            ON CONFLICT (user_id, allergen_id) DO UPDATE SET severity = EXCLUDED.severity
            """,
            (uid, severity, ingredient_id),
        )
        conn.commit()
        return ok("Sensitivity saved successfully.", {"ingredient": ingredient, "severity": severity}, 201)


def add_restriction(username, restriction):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    value = (restriction or "").strip()
    if not value:
        return fail("Restriction is required.")
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT restriction_id FROM dietary_restrictions WHERE restriction=%s", (value,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO dietary_restrictions(restriction) VALUES(%s) RETURNING restriction_id",
                (value,),
            )
            restriction_id = cursor.fetchone()[0]
        else:
            restriction_id = row[0]
        cursor.execute(
            """
            INSERT INTO user_restrictions(user_id, restriction_id)
            VALUES(%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (uid, restriction_id),
        )
        conn.commit()
        return ok("Restriction saved successfully.", {"restriction": value}, 201)


def remove_allergen(username, allergen):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient=%s", ((allergen or "").lower(),))
        row = cursor.fetchone()
        if row is None:
            return fail("Sensitivity not found.", 404)
        cursor.execute(
            "DELETE FROM user_allergies WHERE user_id=%s AND allergen_id=%s",
            (uid, row[0]),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Sensitivity not found.", 404)
        return ok("Sensitivity removed successfully.")


def remove_restriction(username, restriction):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT restriction_id FROM dietary_restrictions WHERE restriction=%s", (restriction,))
        row = cursor.fetchone()
        if row is None:
            return fail("Restriction not found.", 404)
        cursor.execute(
            "DELETE FROM user_restrictions WHERE user_id=%s AND restriction_id=%s",
            (uid, row[0]),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Restriction not found.", 404)
        return ok("Restriction removed successfully.")


def update_allergen_severity(username, allergen, new_severity):
    if new_severity not in {"low", "medium", "high"}:
        return fail("Severity must be low, medium, or high.")
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient=%s", ((allergen or "").lower(),))
        row = cursor.fetchone()
        if row is None:
            return fail("Sensitivity not found.", 404)
        cursor.execute(
            "UPDATE user_allergies SET severity=%s WHERE user_id=%s AND allergen_id=%s",
            (new_severity, uid, row[0]),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Sensitivity not found.", 404)
        return ok("Severity updated successfully.", {"ingredient": allergen, "severity": new_severity})
