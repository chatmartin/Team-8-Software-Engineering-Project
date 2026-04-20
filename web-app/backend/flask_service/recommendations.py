"""Hybrid meal recommendations with deterministic scoring and optional AI text."""

import hashlib
import json
import urllib.error
import urllib.request

from .food_tracking import get_cached_meals, search_meal
from .globals import OPENAI_API_KEY, OPENAI_MODEL, fail, get_db_conn, ok
from .goal_tracking import daily_nutrient_progress, get_goals
from .restrictions import get_preferences


DEFAULT_QUERIES = ["balanced dinner", "high protein lunch", "vegetable bowl"]
NUTRIENT_UNITS = {
    "calories": "kcal",
    "protein": "g",
    "carbohydrates": "g",
    "fat": "g",
    "fiber": "g",
    "sugar": "g",
    "sodium": "mg",
}


def _amount(value):
    if isinstance(value, dict):
        return value.get("amount", 0) or 0
    return value or 0


def _nutrient_total(value):
    if isinstance(value, dict):
        return value.get("total", 0) or 0
    return value or 0


def _score_meal(meal, goals, progress, sensitivities):
    score = 50
    signals = []
    flags = list(meal.get("flags", []))
    ingredients = " ".join(item["name"] for item in meal.get("ingredients", []))

    for sensitivity in sensitivities:
        ingredient = sensitivity["ingredient"]
        if ingredient not in ingredients:
            continue
        severity = sensitivity["severity"]
        if severity == "high":
            return None
        if severity == "medium":
            score -= 20
            signals.append(f"penalized for medium sensitivity to {ingredient}")
        else:
            score -= 7
            flags.append(ingredient)
            signals.append(f"contains low-priority dislike: {ingredient}")

    nutrients = meal.get("nutrients", {})
    for goal in goals:
        nutrient = goal["nutrient"]
        if nutrient not in nutrients:
            continue
        target = float(goal.get("target") or 0)
        if target <= 0:
            continue
        current = float(_nutrient_total(progress.get(nutrient, {})))
        meal_amount = float(_amount(nutrients[nutrient]))
        remaining = target - current
        if goal.get("min_max") == "max":
            if current + meal_amount > target:
                score -= min(25, ((current + meal_amount - target) / target) * 30)
                signals.append(f"may push {nutrient} over target")
        elif remaining > 0:
            contribution = min(meal_amount / remaining, 1.0)
            score += contribution * 15
            signals.append(f"helps with {nutrient}")

    if not signals:
        signals.append("fits current saved preferences")
    meal["flags"] = sorted(set(flags))
    return {"score": round(max(0, min(100, score)), 1), "signals": signals}


def _local_explanation(meal, signals):
    if meal.get("flags"):
        return f"{meal['meal']} is a decent match, but note: {', '.join(meal['flags'])}."
    return f"{meal['meal']} is recommended because it {signals[0]}."


def _recipe_id(seed):
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return 1_700_000_000 + (int(digest[:8], 16) % 200_000_000)


def _nutrients(calories, protein, carbohydrates, fat, fiber=4, sugar=6, sodium=320):
    return {
        "calories": {"amount": calories, "unit": "kcal"},
        "protein": {"amount": protein, "unit": "g"},
        "carbohydrates": {"amount": carbohydrates, "unit": "g"},
        "fat": {"amount": fat, "unit": "g"},
        "fiber": {"amount": fiber, "unit": "g"},
        "sugar": {"amount": sugar, "unit": "g"},
        "sodium": {"amount": sodium, "unit": "mg"},
    }


def _ingredient(name, amount, unit):
    return {"name": name, "amount": amount, "unit": unit}


def _meal_template(query, title, ingredients, nutrients, steps, summary):
    recipe_id = _recipe_id(f"{query}:{title}")
    return {
        "meal_id": f"ai-{recipe_id}",
        "recipe_id": recipe_id,
        "meal": title,
        "ingredients": ingredients,
        "nutrients": nutrients,
        "flags": [],
        "generated": True,
        "recipe": {
            "servings": 1,
            "ready_in_minutes": 15,
            "summary": summary,
            "steps": steps,
        },
    }


def _local_generated_meals(query):
    normalized = (query or "balanced meal").strip().lower()
    if "yogurt" in normalized:
        return [
            _meal_template(
                query,
                "Greek Yogurt Protein Bowl",
                [
                    _ingredient("plain greek yogurt", 1, "cup"),
                    _ingredient("blueberries", 0.5, "cup"),
                    _ingredient("granola", 0.25, "cup"),
                    _ingredient("chia seeds", 1, "tbsp"),
                    _ingredient("honey", 1, "tsp"),
                ],
                _nutrients(385, 29, 48, 10, fiber=8, sugar=24, sodium=115),
                [
                    "Spoon the Greek yogurt into a bowl.",
                    "Top with blueberries, granola, and chia seeds.",
                    "Drizzle honey over the bowl and serve cold.",
                ],
                "A high-protein yogurt bowl with fruit, crunch, and fiber.",
            ),
            _meal_template(
                query,
                "Savory Cucumber Yogurt Plate",
                [
                    _ingredient("plain greek yogurt", 1, "cup"),
                    _ingredient("cucumber", 0.5, "cup"),
                    _ingredient("cherry tomatoes", 0.5, "cup"),
                    _ingredient("olive oil", 1, "tsp"),
                    _ingredient("whole grain pita", 1, "small"),
                ],
                _nutrients(330, 25, 39, 9, fiber=6, sugar=10, sodium=420),
                [
                    "Spread yogurt onto a plate and season lightly.",
                    "Add chopped cucumber and tomatoes.",
                    "Drizzle olive oil and serve with warm pita.",
                ],
                "A savory yogurt meal that works as a light lunch or snack plate.",
            ),
            _meal_template(
                query,
                "Yogurt Smoothie Meal",
                [
                    _ingredient("plain yogurt", 1, "cup"),
                    _ingredient("banana", 1, "medium"),
                    _ingredient("peanut butter", 1, "tbsp"),
                    _ingredient("rolled oats", 0.25, "cup"),
                    _ingredient("milk", 0.5, "cup"),
                ],
                _nutrients(455, 24, 62, 14, fiber=7, sugar=28, sodium=180),
                [
                    "Add yogurt, banana, peanut butter, oats, and milk to a blender.",
                    "Blend until smooth.",
                    "Pour into a glass and let it sit for two minutes to thicken.",
                ],
                "A filling yogurt smoothie with balanced carbs, protein, and fats.",
            ),
        ]

    readable = normalized.replace("-", " ")
    return [
        _meal_template(
            query,
            f"{readable.title()} Protein Bowl",
            [
                _ingredient(readable, 1, "serving"),
                _ingredient("brown rice", 0.5, "cup"),
                _ingredient("mixed greens", 1, "cup"),
                _ingredient("olive oil vinaigrette", 1, "tbsp"),
            ],
            _nutrients(520, 32, 55, 18, fiber=9, sugar=7, sodium=520),
            [
                "Prepare the base ingredients.",
                "Layer rice, greens, and the main ingredient in a bowl.",
                "Add vinaigrette and toss before serving.",
            ],
            f"A balanced bowl built around {readable}.",
        ),
        _meal_template(
            query,
            f"Quick {readable.title()} Wrap",
            [
                _ingredient(readable, 1, "serving"),
                _ingredient("whole wheat tortilla", 1, "large"),
                _ingredient("lettuce", 0.5, "cup"),
                _ingredient("tomato", 0.25, "cup"),
                _ingredient("yogurt sauce", 2, "tbsp"),
            ],
            _nutrients(430, 27, 48, 14, fiber=7, sugar=6, sodium=610),
            [
                "Warm the tortilla.",
                "Fill with the main ingredient, lettuce, tomato, and sauce.",
                "Roll tightly and slice before serving.",
            ],
            f"A fast wrap option for a {readable} craving.",
        ),
    ]


def _ai_generate_meals(query, goals, sensitivities):
    if not OPENAI_API_KEY:
        return []
    body = json.dumps(
        {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Generate meal recommendations as strict JSON. Return an array of 3 objects with meal, "
                        "ingredients, nutrients, recipe, and explanation. Nutrients must include calories, protein, "
                        "carbohydrates, and fat with numeric amount and unit."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "query": query,
                            "goals": goals[:6],
                            "sensitivities": sensitivities,
                        }
                    ),
                },
            ],
            "temperature": 0.4,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            meals = json.loads(content)
            generated = []
            for meal in meals[:3]:
                title = meal.get("meal")
                if not title:
                    continue
                generated.append(
                    {
                        "meal_id": f"ai-{_recipe_id(f'{query}:{title}')}",
                        "recipe_id": _recipe_id(f"{query}:{title}"),
                        "meal": title,
                        "ingredients": meal.get("ingredients", []),
                        "nutrients": meal.get("nutrients", {}),
                        "flags": [],
                        "generated": True,
                        "recipe": meal.get("recipe", {}),
                        "explanation": meal.get("explanation"),
                    }
                )
            return generated
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError, TypeError):
        return []


def _ensure_generated_meals(meals):
    conn = get_db_conn()
    if conn is None:
        return
    with conn.cursor() as cursor:
        cursor.execute("SELECT name, nutrient_id FROM nutrients")
        nutrient_ids = {name: nutrient_id for name, nutrient_id in cursor.fetchall()}
        for meal in meals:
            cursor.execute("SELECT meal_id FROM meals WHERE recipe_id = %s", (meal["recipe_id"],))
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO meals (meal, recipe_id) VALUES (%s, %s) RETURNING meal_id",
                    (meal["meal"], meal["recipe_id"]),
                )
                meal_id = cursor.fetchone()[0]
            else:
                meal_id = row[0]
            meal["meal_id"] = meal_id

            for name, nutrient in meal.get("nutrients", {}).items():
                if name not in nutrient_ids:
                    unit = nutrient.get("unit") or NUTRIENT_UNITS.get(name, "g")
                    cursor.execute(
                        "INSERT INTO nutrients (name, unit) VALUES (%s, %s) RETURNING nutrient_id",
                        (name, unit),
                    )
                    nutrient_ids[name] = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO meal_nutrients (meal_id, nutrient_id, amount)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (meal_id, nutrient_ids[name], nutrient.get("amount", 0)),
                )

            for ingredient in meal.get("ingredients", []):
                name = ingredient.get("name", "").lower()
                if not name:
                    continue
                cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient = %s", (name,))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("INSERT INTO ingredients (ingredient) VALUES (%s) RETURNING ingredient_id", (name,))
                    ingredient_id = cursor.fetchone()[0]
                else:
                    ingredient_id = row[0]
                cursor.execute(
                    """
                    INSERT INTO meal_ingredients (meal_id, ingredient_id, amount, unit)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (meal_id, ingredient_id, ingredient.get("amount"), ingredient.get("unit")),
                )
        conn.commit()


def _ai_explain(meals):
    if not OPENAI_API_KEY or not meals:
        return {}
    compact = [
        {
            "meal": meal["meal"],
            "score": meal["score"],
            "signals": meal["score_signals"][:3],
            "flags": meal.get("flags", []),
        }
        for meal in meals[:5]
    ]
    body = json.dumps(
        {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Write concise food recommendation explanations. Do not give medical advice.",
                },
                {
                    "role": "user",
                    "content": "Explain these ranked meals in one short sentence each as JSON keyed by meal name: "
                    + json.dumps(compact),
                },
            ],
            "temperature": 0.3,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            return json.loads(content)
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError):
        return {}


def get_recommendations(username, query=None):
    goals_payload, goals_status = get_goals(username)
    if goals_status >= 400:
        return goals_payload, goals_status
    progress_payload, progress_status = daily_nutrient_progress(username)
    if progress_status >= 400:
        return progress_payload, progress_status
    prefs_payload, prefs_status = get_preferences(username)
    if prefs_status >= 400:
        return prefs_payload, prefs_status

    goals = goals_payload["data"].get("goals", [])
    progress = progress_payload["data"] or {}
    sensitivities = prefs_payload["data"].get("sensitivities", [])
    candidates = []

    if query:
        results = search_meal(query, username)
        if results:
            candidates.extend(results)
        if not candidates:
            generated = _ai_generate_meals(query, goals, sensitivities)
            if not generated:
                generated = _local_generated_meals(query)
            _ensure_generated_meals(generated)
            candidates.extend(generated)
    if not candidates:
        for default_query in DEFAULT_QUERIES:
            results = search_meal(default_query, username)
            if results:
                candidates.extend(results)
                break
    if not candidates:
        candidates.extend(get_cached_meals(username=username, limit=20))

    ranked = []
    seen = set()
    for meal in candidates:
        recipe_id = meal.get("recipe_id")
        if recipe_id in seen:
            continue
        seen.add(recipe_id)
        score = _score_meal(meal, goals, progress, sensitivities)
        if score is None:
            continue
        meal["score"] = score["score"]
        meal["score_signals"] = score["signals"]
        meal["explanation"] = _local_explanation(meal, score["signals"])
        ranked.append(meal)

    ranked.sort(key=lambda item: item["score"], reverse=True)
    ranked = ranked[:8]
    ai_text = _ai_explain(ranked)
    for meal in ranked:
        if meal["meal"] in ai_text:
            meal["explanation"] = ai_text[meal["meal"]]

    return ok("Recommendations generated successfully.", ranked)


def save_recommendation_feedback(username, recipe_id, action):
    if action not in {"saved", "dismissed", "logged", "disliked"}:
        return fail("Feedback action must be saved, dismissed, logged, or disliked.")
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM login_info WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user is None:
            return fail("User not found.", 404)
        cursor.execute("SELECT meal_id FROM meals WHERE recipe_id=%s", (recipe_id,))
        meal = cursor.fetchone()
        if meal is None:
            return fail("Meal not found.", 404)
        cursor.execute(
            """
            INSERT INTO recommendation_feedback(user_id, meal_id, action)
            VALUES(%s, %s, %s)
            """,
            (user[0], meal[0], action),
        )
        conn.commit()
        return ok("Recommendation feedback saved successfully.", {"recipe_id": recipe_id, "action": action}, 201)
