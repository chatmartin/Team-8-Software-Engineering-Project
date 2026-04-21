"""Nutrition goals and progress tracking."""

from .globals import fail, get_db_conn, ok
from .standard_goals import recommended_goal


def _user_id(cursor, username):
    cursor.execute("SELECT user_id FROM login_info WHERE username = %s", (username,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_goals(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT n.name, ug.target_amount, n.unit, ug.is_max
            FROM user_goals ug
            JOIN nutrients n ON ug.nutrient_id = n.nutrient_id
            WHERE ug.user_id=%s
            ORDER BY n.name
            """,
            (uid,),
        )
        goals = [
            {"nutrient": row[0], "target": row[1], "unit": row[2], "min_max": "max" if row[3] else "min"}
            for row in cursor.fetchall()
        ]
        rec_payload, rec_status = recommended_goal(username)
        recommended = rec_payload["data"] if rec_status < 400 else {}
        return ok("Goals obtained successfully.", {"goals": goals, "recommended": recommended})


def add_goal(username, nutrient, amount, min_max):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT nutrient_id, unit FROM nutrients WHERE name = %s", ((nutrient or "").lower(),))
        row = cursor.fetchone()
        if row is None:
            return fail("Nutrient not found.", 404)
        is_max = min_max == "max"
        cursor.execute(
            """
            INSERT INTO user_goals(user_id, nutrient_id, target_amount, is_max)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, nutrient_id) DO UPDATE SET
                target_amount = EXCLUDED.target_amount,
                is_max = EXCLUDED.is_max
            """,
            (uid, row[0], amount, is_max),
        )
        conn.commit()
        return ok(
            "Goal saved successfully.",
            {"nutrient": nutrient, "target": amount, "unit": row[1], "min_max": min_max},
            201,
        )


def update_goal(username, nutrient, amount, min_max):
    return add_goal(username, nutrient, amount, min_max)


def remove_goal(username, nutrient):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT nutrient_id FROM nutrients WHERE name = %s", ((nutrient or "").lower(),))
        row = cursor.fetchone()
        if row is None:
            return fail("Nutrient not found.", 404)
        cursor.execute("DELETE FROM user_goals WHERE user_id = %s AND nutrient_id = %s", (uid, row[0]))
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Goal not found.", 404)
        return ok("Goal removed successfully.")


def weekly_nutrient_progress(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT n.name, SUM(mn.amount) / NULLIF(COUNT(DISTINCT DATE(um.eaten_at)), 0), n.unit
            FROM user_meals um
            JOIN meal_nutrients mn ON um.meal_id = mn.meal_id
            JOIN nutrients n ON mn.nutrient_id = n.nutrient_id
            WHERE um.user_id = %s
              AND um.eaten_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY n.name, n.unit
            ORDER BY n.name
            """,
            (uid,),
        )
        data = {
            name: {"avg_per_day": avg or 0, "unit": unit}
            for name, avg, unit in cursor.fetchall()
        }
        return ok("Weekly nutrient progress obtained successfully.", data)


def daily_nutrient_progress(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT n.name, COALESCE(SUM(mn.amount), 0), n.unit
            FROM user_meals um
            JOIN meal_nutrients mn ON um.meal_id = mn.meal_id
            JOIN nutrients n ON mn.nutrient_id = n.nutrient_id
            WHERE um.user_id = %s
              AND (um.eaten_at AT TIME ZONE 'UTC')::date = CURRENT_DATE
            GROUP BY n.name, n.unit
            ORDER BY n.name
            """,
            (uid,),
        )
        data = {name: {"total": total or 0, "unit": unit} for name, total, unit in cursor.fetchall()}
        return ok("Daily nutrient progress obtained successfully.", data)
