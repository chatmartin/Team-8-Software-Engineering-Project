"""Spoonacular recipe API integration."""

import requests

from .globals import SPOONACULAR_API_KEY, get_db_conn


def fetch_meals(meal_name, diets, allergens, excludes):
    if not SPOONACULAR_API_KEY:
        return None
    conn = get_db_conn()
    if conn is None:
        return None
    with conn.cursor() as cursor:
        url = "https://api.spoonacular.com/recipes/complexSearch"
        res = requests.get(
            url,
            params={
                "query": meal_name,
                "number": 8,
                "diet": ",".join(diets) if diets else None,
                "intolerances": ",".join(allergens) if allergens else None,
                "excludeIngredients": ",".join(excludes) if excludes else None,
                "addRecipeInformation": True,
                "fillIngredients": True,
                "addRecipeNutrition": True,
                "apiKey": SPOONACULAR_API_KEY,
            },
            timeout=20,
        )
        if res.status_code != 200:
            return None

        results = res.json().get("results", [])
        meals = []

        cursor.execute("SELECT name, unit FROM nutrients")
        nutrient_map = {name: unit for name, unit in cursor.fetchall()}

        for r in results:
            if "kosher" in diets and not (r.get("dairyFree") or r.get("vegetarian")):
                continue
            nutrients = {}
            for n in r.get("nutrition", {}).get("nutrients", []):
                name = n["name"].lower()
                amount = n["amount"]

                api_unit = normalize_unit_name(n["unit"])
                db_unit = normalize_unit_name(nutrient_map.get(name))

                if not db_unit:
                    db_unit = api_unit
                    cursor.execute(
                        "INSERT INTO nutrients (name, unit) VALUES (%s, %s)",
                        (name, db_unit)
                    )
                    conn.commit()
                    nutrient_map[name] = db_unit

                if api_unit != db_unit:
                    amount = normalize_unit(amount, api_unit, db_unit)

                nutrients[name.lower()] = {"amount": amount}
            meals.append({
                "recipe_id": r["id"],
                "meal": r["title"],
                "ingredients": [
                    {
                        "name": i["name"].lower(),
                        "amount": i.get("amount"),
                        "unit": i.get("unit"),
                    }
                    for i in r.get("extendedIngredients", [])
                ],
                "nutrients": nutrients,
                "recipe": {
                    "servings": r.get("servings"),
                    "ready_in_minutes": r.get("readyInMinutes"),
                    "source_url": r.get("sourceUrl"),
                    "summary": r.get("summary"),
                    "steps": [
                        step.get("step")
                        for instruction in r.get("analyzedInstructions", [])
                        for step in instruction.get("steps", [])
                        if step.get("step")
                    ],
                },
            })

        return meals


def normalize_unit(amount, from_unit, to_unit):
    if from_unit == to_unit:
        return amount

    # mg <-> g
    if from_unit == "mg" and to_unit == "g":
        return amount / 1000
    if from_unit == "g" and to_unit == "mg":
        return amount * 1000

    # ug <-> mg
    if from_unit == "ug" and to_unit == "mg":
        return amount / 1000
    if from_unit == "mg" and to_unit == "ug":
        return amount * 1000

    # ug <-> g
    if from_unit == "ug" and to_unit == "g":
        return amount / 1_000_000
    if from_unit == "g" and to_unit == "ug":
        return amount * 1_000_000

    return amount


def normalize_unit_name(unit):
    if unit in ["\u03bcg", "\u00b5g", "ug", "mcg"]:
        return "ug"
    return unit
