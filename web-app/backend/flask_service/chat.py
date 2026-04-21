"""Gemini-backed recommendation chat."""

import json

from .bio_data import get_bio_data
from .food_tracking import get_meals
from .gemini import GeminiError, generate_text
from .globals import GEMINI_API_KEY, GEMINI_MODEL, fail, ok
from .goal_tracking import daily_nutrient_progress, get_goals
from .restrictions import get_preferences


def _nutrient_summary(nutrients):
    if not isinstance(nutrients, dict):
        return {}
    summary = {}
    for name in ("calories", "protein", "carbohydrates", "fat", "fiber", "sodium", "sugar"):
        value = nutrients.get(name)
        if isinstance(value, dict):
            summary[name] = {
                "amount": value.get("amount") or value.get("total") or value.get("avg_per_day"),
                "unit": value.get("unit"),
            }
        elif value is not None:
            summary[name] = value
    return summary


def _compact_recommendation(meal):
    nutrients = meal.get("nutrients", {})
    recipe = meal.get("recipe", {}) or {}
    return {
        "meal": meal.get("meal"),
        "score": meal.get("score"),
        "explanation": meal.get("explanation"),
        "score_signals": meal.get("score_signals", [])[:5],
        "flags": meal.get("flags", [])[:5],
        "ingredients": [item.get("name") for item in meal.get("ingredients", [])[:8]],
        "nutrients": _nutrient_summary(nutrients),
        "recipe": {
            "summary": recipe.get("summary"),
            "ready_in_minutes": recipe.get("ready_in_minutes"),
            "servings": recipe.get("servings"),
        },
    }


def _compact_meal(meal):
    return {
        "meal": meal.get("meal"),
        "eaten_at": meal.get("eaten_at"),
        "recipe_id": meal.get("recipe_id"),
        "nutrients": _nutrient_summary(meal.get("nutrients", {})),
        "ingredients": [item.get("name") for item in meal.get("ingredients", [])[:6]],
    }


def _context(username, recommendations):
    profile_payload, _profile_status = get_bio_data(username)
    prefs_payload, _prefs_status = get_preferences(username)
    goals_payload, _goals_status = get_goals(username)
    progress_payload, _progress_status = daily_nutrient_progress(username)
    meals_payload, _meals_status = get_meals(username)

    return {
        "username": username,
        "profile": profile_payload.get("data"),
        "preferences": prefs_payload.get("data"),
        "goals": goals_payload.get("data"),
        "today_progress": progress_payload.get("data"),
        "recent_meals": [_compact_meal(meal) for meal in (meals_payload.get("data") or [])[:10]],
        "current_recommendations": [
            _compact_recommendation(meal) for meal in (recommendations or [])[:8]
        ],
    }


def _fallback_reply(message, recommendations, progress):
    first = recommendations[0] if recommendations else None
    if not first:
        return (
            "I can chat about recommendations once the app has a few meals loaded. "
            "Try searching for a food like yogurt, chicken, or pasta first."
        )
    protein = first.get("nutrients", {}).get("protein", {}).get("amount", 0)
    calories = first.get("nutrients", {}).get("calories", {}).get("amount", 0)
    if "protein" in message.lower():
        return f"{first['meal']} is a good starting point with about {protein}g protein."
    if "calorie" in message.lower():
        return f"{first['meal']} has about {calories} calories based on the current recipe data."
    if "ingredient" in message.lower():
        ingredients = ", ".join(item.get("name", "") for item in first.get("ingredients", [])[:6])
        return f"{first['meal']} uses {ingredients}. Use Show ingredients for the full list."
    if any(word in message.lower() for word in ("tomorrow", "morning", "breakfast", "follow")):
        return (
            f"If you go with {first['meal']}, follow it tomorrow morning with a protein-forward breakfast "
            "like Greek yogurt with fruit, eggs with vegetables, or oatmeal with nuts. That keeps the next "
            "meal lighter while still helping protein and fiber."
        )
    logged = progress.get("calories", {}).get("total", 0) if isinstance(progress, dict) else 0
    return (
        f"My first pick is {first['meal']}. It has about {calories} calories and {protein}g protein. "
        f"You have logged about {logged} calories today."
    )


def chat_with_model(username, message, history=None, recommendations=None):
    try:
        if not username:
            return fail("Username is required.")
        if not message:
            return fail("Message is required.")

        context = _context(username, recommendations or [])
        progress = context.get("today_progress") or {}
        if not GEMINI_API_KEY:
            return ok(
                "Gemini API key is not configured; using local fallback chat.",
                {
                    "reply": _fallback_reply(message, recommendations or [], progress),
                    "model": "local-fallback",
                },
            )

        system_instruction = (
            "You are Ctrl+Eat's in-app meal planning assistant. Answer using the CURRENT_CONTEXT JSON first. "
            "Treat current_recommendations as visible recommendation cards and recent_meals as the user's meal log. "
            "If the user mentions a recommended meal by name, connect your answer to that exact meal even if it is not a breakfast item. "
            "For follow-up meal advice, suggest a practical next meal that complements the logged/recommended meal using macros, goals, preferences, and allergies when available. "
            "If context is missing, say what is missing and still give a useful next step from the available data. "
            "Do not say the recommendations are unavailable when current_recommendations contains items. "
            "Avoid medical diagnosis or treatment advice. Keep answers complete, specific, and under 180 words."
        )
        context_message = (
            "CURRENT_CONTEXT JSON. Use this as the source of truth for this reply:\n"
            + json.dumps(context, default=str)
        )
        messages = [("user", context_message)]

        for item in (history or [])[-8:]:
            role = "model" if item.get("role") == "assistant" else "user"
            messages.append((role, item.get("text", "")))
        messages.append(("user", message))

        reply, payload = generate_text(
            system_instruction,
            messages,
            temperature=0.4,
            max_tokens=900,
        )
    except GeminiError as error:
        return fail(f"Gemini chat request failed: {error}", 502)
    except Exception as error:
        return fail(f"Chat request failed: {type(error).__name__}: {error}", 500)

    return ok(
        "Chat response generated successfully.",
        {
            "reply": reply,
            "model": GEMINI_MODEL,
            "response_id": payload.get("responseId"),
        },
    )
