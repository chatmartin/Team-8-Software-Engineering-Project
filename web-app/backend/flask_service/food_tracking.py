"""Meal search and tracking logic."""

from .globals import CUSTOM_RESTRICTION_EXCLUDES, VALID_DIETS, fail, get_db_conn, ok
from .spoonacular_api_calls import fetch_meals


def _user_id(cursor, username):
    cursor.execute("SELECT user_id FROM login_info WHERE username = %s", (username,))
    row = cursor.fetchone()
    return row[0] if row else None


def _serialize_dt(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _fallback_recipe(meal_name, ingredients):
    ingredient_names = [item["name"] for item in ingredients[:6]]
    prep_list = ", ".join(ingredient_names) if ingredient_names else "the prepared ingredients"
    return {
        "servings": 1,
        "ready_in_minutes": 15,
        "steps": [
            f"Gather {prep_list}.",
            "Combine the ingredients and season to taste.",
            "Serve chilled or warmed depending on the meal style.",
        ],
        "summary": f"A simple recipe outline for {meal_name}.",
    }


def query_builder(meal_query, username, cursor):
    cursor.execute(
        """
        SELECT i.ingredient, a.severity
        FROM user_allergies a
        JOIN ingredients i ON a.allergen_id = i.ingredient_id
        JOIN login_info l ON a.user_id = l.user_id
        WHERE l.username = %s AND a.severity IN ('high', 'medium')
        """,
        (username,),
    )
    allergens = []
    excludes = []
    for ingredient, severity in cursor.fetchall():
        if severity == "high":
            allergens.append(ingredient)
        else:
            excludes.append(ingredient)

    cursor.execute(
        """
        SELECT r.restriction
        FROM user_restrictions u
        JOIN dietary_restrictions r ON u.restriction_id = r.restriction_id
        JOIN login_info l ON u.user_id = l.user_id
        WHERE l.username = %s
        """,
        (username,),
    )
    diets = []
    for (restriction,) in cursor.fetchall():
        if restriction in VALID_DIETS:
            diets.append(restriction)
        for excluded in CUSTOM_RESTRICTION_EXCLUDES.get(restriction, []):
            if excluded not in excludes:
                excludes.append(excluded)

    return [(meal_query or "").lower(), sorted(diets), sorted(allergens), sorted(excludes)]


def cache_results(query_list, signature, cursor, conn):
    cursor.execute(
        """
        INSERT INTO queries (query_signature)
        VALUES (%s)
        ON CONFLICT (query_signature) DO NOTHING
        """,
        (signature,),
    )
    conn.commit()

    cursor.execute("SELECT query_id FROM queries WHERE query_signature = %s", (signature,))
    qid = cursor.fetchone()[0]

    meal_results = fetch_meals(query_list[0], query_list[1], query_list[2], query_list[3])
    if meal_results is None:
        return False

    for rank, meal in enumerate(meal_results, start=1):
        cursor.execute("SELECT meal_id FROM meals WHERE recipe_id = %s", (meal["recipe_id"],))
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO meals (meal, recipe_id) VALUES (%s, %s)",
                (meal["meal"], meal["recipe_id"]),
            )
            conn.commit()
            cursor.execute("SELECT meal_id FROM meals WHERE recipe_id = %s", (meal["recipe_id"],))
            mid = cursor.fetchone()[0]

            for nutrient, val in meal["nutrients"].items():
                cursor.execute("SELECT nutrient_id FROM nutrients WHERE name = %s", (nutrient,))
                nrow = cursor.fetchone()
                if nrow is None:
                    continue
                cursor.execute(
                    """
                    INSERT INTO meal_nutrients (meal_id, nutrient_id, amount)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (mid, nrow[0], val["amount"]),
                )

            for ing in meal["ingredients"]:
                ingredient = ing["name"].lower()
                cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient = %s", (ingredient,))
                irow = cursor.fetchone()
                if irow is None:
                    cursor.execute("INSERT INTO ingredients (ingredient) VALUES (%s)", (ingredient,))
                    conn.commit()
                    cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient = %s", (ingredient,))
                    iid = cursor.fetchone()[0]
                else:
                    iid = irow[0]
                cursor.execute(
                    """
                    INSERT INTO meal_ingredients (meal_id, ingredient_id, amount, unit)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (mid, iid, ing.get("amount"), ing.get("unit")),
                )
            conn.commit()
        else:
            mid = row[0]

        cursor.execute(
            """
            INSERT INTO meal_queries (meal_id, query_id, rank)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (mid, qid, rank),
        )

    conn.commit()
    return True


def _hydrate_meal(cursor, mid, meal_name, recipe_id, username=None):
    meal_data = {
        "meal_id": mid,
        "meal": meal_name,
        "recipe_id": recipe_id,
        "ingredients": [],
        "nutrients": {},
        "flags": [],
        "recipe": None,
    }

    cursor.execute(
        """
        SELECT i.ingredient, mi.amount, mi.unit
        FROM meal_ingredients mi
        JOIN ingredients i ON mi.ingredient_id = i.ingredient_id
        WHERE mi.meal_id = %s
        ORDER BY i.ingredient
        """,
        (mid,),
    )
    for name, amount, unit in cursor.fetchall():
        meal_data["ingredients"].append({"name": name, "amount": amount, "unit": unit})

    cursor.execute(
        """
        SELECT n.name, mn.amount, n.unit
        FROM meal_nutrients mn
        JOIN nutrients n ON mn.nutrient_id = n.nutrient_id
        WHERE mn.meal_id = %s
        """,
        (mid,),
    )
    for name, amount, unit in cursor.fetchall():
        meal_data["nutrients"][name] = {"amount": amount, "unit": unit}

    meal_data["recipe"] = _fallback_recipe(meal_name, meal_data["ingredients"])

    if username:
        cursor.execute(
            """
            SELECT i.ingredient
            FROM user_allergies u
            JOIN ingredients i ON i.ingredient_id = u.allergen_id
            JOIN login_info l ON l.user_id = u.user_id
            WHERE l.username = %s AND u.severity = 'low'
            """,
            (username,),
        )
        dislikes = [row[0] for row in cursor.fetchall()]
        ingredient_names = [item["name"] for item in meal_data["ingredients"]]
        for dislike in dislikes:
            if any(dislike in name for name in ingredient_names):
                meal_data["flags"].append(dislike)

    return meal_data


def search_meal(meal_query, username):
    conn = get_db_conn()
    if conn is None:
        return None

    with conn.cursor() as cursor:
        query_list = query_builder(meal_query, username, cursor)
        signature = f"{query_list[0]}|{','.join(query_list[1])}|{','.join(query_list[2])}|{','.join(query_list[3])}"

        cursor.execute("SELECT query_id FROM queries WHERE query_signature = %s", (signature,))
        if cursor.fetchone() is None and not cache_results(query_list, signature, cursor, conn):
            return None

        cursor.execute(
            """
            SELECT m.meal_id, m.meal, m.recipe_id
            FROM meal_queries mq
            JOIN queries q ON mq.query_id = q.query_id
            JOIN meals m ON mq.meal_id = m.meal_id
            WHERE q.query_signature = %s
            ORDER BY mq.rank
            """,
            (signature,),
        )
        return [_hydrate_meal(cursor, *row, username=username) for row in cursor.fetchall()]


def get_cached_meals(username=None, limit=25):
    conn = get_db_conn()
    if conn is None:
        return []
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT meal_id, meal, recipe_id
            FROM meals
            ORDER BY meal_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [_hydrate_meal(cursor, *row, username=username) for row in cursor.fetchall()]


def get_meals(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            """
            SELECT m.meal_id, m.meal, m.recipe_id, u.eaten_at
            FROM user_meals u
            JOIN meals m ON m.meal_id = u.meal_id
            WHERE u.user_id = %s
            ORDER BY u.eaten_at DESC
            """,
            (uid,),
        )
        data = [
            {
                "user_meal_id": f"{row[2]}:{_serialize_dt(row[3])}",
                "meal_id": row[0],
                "meal": row[1],
                "recipe_id": row[2],
                "eaten_at": _serialize_dt(row[3]),
            }
            for row in cursor.fetchall()
        ]
        return ok("Meals obtained successfully.", data)


def add_meal(username, recipe_id, eaten_at):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT meal_id, meal FROM meals WHERE recipe_id = %s", (recipe_id,))
        row = cursor.fetchone()
        if row is None:
            return fail("Meal must be searched before it can be logged.", 404)
        cursor.execute(
            "INSERT INTO user_meals (user_id, meal_id, eaten_at) VALUES (%s, %s, %s)",
            (uid, row[0], eaten_at),
        )
        conn.commit()
        return ok(
            "Meal added successfully.",
            {"meal_id": row[0], "meal": row[1], "recipe_id": recipe_id, "eaten_at": eaten_at},
            201,
        )


def remove_meal(username, user_meal_id=None, recipe_id=None, eaten_at=None):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT meal_id FROM meals WHERE recipe_id = %s", (recipe_id,))
        row = cursor.fetchone()
        if row is None:
            return fail("Meal not found.", 404)
        cursor.execute(
            "DELETE FROM user_meals WHERE meal_id = %s AND user_id = %s AND eaten_at = %s",
            (row[0], uid, eaten_at),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Meal log not found.", 404)
        return ok("Meal removed successfully.")


def update_meal_time(username, user_meal_id, eaten_at):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute(
            "UPDATE user_meals SET eaten_at = %s WHERE user_meal_id = %s AND user_id = %s",
            (eaten_at, user_meal_id, uid),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Meal log not found.", 404)
        return ok("Meal time updated successfully.")


def update_meal(username, user_meal_id, new_recipe_id):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        uid = _user_id(cursor, username)
        if uid is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT meal_id FROM meals WHERE recipe_id = %s", (new_recipe_id,))
        row = cursor.fetchone()
        if row is None:
            return fail("Replacement meal must be searched first.", 404)
        cursor.execute(
            "UPDATE user_meals SET meal_id = %s WHERE user_meal_id = %s AND user_id = %s",
            (row[0], user_meal_id, uid),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return fail("Meal log not found.", 404)
        return ok("Meal updated successfully.")
