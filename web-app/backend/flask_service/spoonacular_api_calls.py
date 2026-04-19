#The purpose of this file is to handle API calls to Spoonacular

from globals import *
import requests

#TODO: modify this to track other potential meal restrictions
def fetch_meals(meal_name,diets,allergens,excludes):
    #connect to the database for eventual unit checking
    conn = get_db_conn()
    with conn.cursor() as cursor:
        #make api call, get top 10 results based on user's search
        url = "https://api.spoonacular.com/recipes/complexSearch"
        res = requests.get(url,params={
            "query": meal_name,
            "number":5,
            "diet": ",".join(diets) if diets else None,
            "intolerances": ",".join(allergens) if allergens else None,
            "excludeIngredients": ",".join(excludes) if excludes else None,
            "addRecipeInformation": True,
            "fillIngredients": True,
            "addRecipeNutrition": True,
            "apiKey":spoon_api_key
        },timeout=20)
        #Make sure call is successful
        if res.status_code != 200:
            return None

        results = res.json().get("results",[])
        if not results:
            return None

        meals = []

        #preload nutrients
        cursor.execute("SELECT name, unit FROM nutrients")
        nutrient_map = {name: unit for name, unit in cursor.fetchall()}

        for r in results:
            if 'kosher' in diets and not(r.get('dairyFree') or r.get('vegetarian')):
                continue
            #set up nutrient dictionary for each nutrient with potential unit conversion and amount
            nutrients = {}
            for n in r.get("nutrition", {}).get("nutrients", []):
                name = n["name"]
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

                nutrients[name.lower()] = {
                    "amount": amount
                }
            #construct meals list
            meals.append({
                "recipe_id": r["id"],
                "meal":r["title"],
                "ingredients":[
                    {
                        "name":i["name"].lower(),
                        "amount":i.get("amount"),
                        "unit":i.get("unit")
                    }
                    for i in r.get("extendedIngredients",[])
                ],
                "flags":{
                    "vegetarian":r.get("vegetarian"),
                    "vegan":r.get("vegan"),
                    "gluten_free":r.get("glutenFree"),
                    "dairy_free":r.get("dairyFree"),
                    "ketogenic":r.get('ketogenic'),
                    "whole30":r.get("whole30")
                },
                "nutrients":nutrients,
            })

        return meals

#written by ai
def normalize_unit(amount, from_unit, to_unit):
    if from_unit == to_unit:
        return amount

    # mg ↔ g
    if from_unit == "mg" and to_unit == "g":
        return amount / 1000
    if from_unit == "g" and to_unit == "mg":
        return amount * 1000

    # µg ↔ mg
    if from_unit == "µg" and to_unit == "mg":
        return amount / 1000
    if from_unit == "mg" and to_unit == "µg":
        return amount * 1000

    # µg ↔ g
    if from_unit == "µg" and to_unit == "g":
        return amount / 1_000_000
    if from_unit == "g" and to_unit == "µg":
        return amount * 1_000_000

    return amount  # fallback

#normalizes micrograms for easy comparison
def normalize_unit_name(unit):
    if unit in ["μg", "ug", "mcg"]:
        return "ug"
    return unit