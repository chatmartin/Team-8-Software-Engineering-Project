"""OpenAI-backed recommendation chat."""

import json
import urllib.error
import urllib.request

from .bio_data import get_bio_data
from .food_tracking import get_meals
from .globals import OPENAI_API_KEY, OPENAI_MODEL, fail, ok
from .goal_tracking import daily_nutrient_progress, get_goals
from .restrictions import get_preferences


def _extract_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]
    chunks = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _compact_recommendation(meal):
    nutrients = meal.get("nutrients", {})
    return {
        "meal": meal.get("meal"),
        "score": meal.get("score"),
        "explanation": meal.get("explanation"),
        "ingredients": [item.get("name") for item in meal.get("ingredients", [])[:8]],
        "nutrients": {
            "calories": nutrients.get("calories"),
            "protein": nutrients.get("protein"),
            "carbohydrates": nutrients.get("carbohydrates"),
            "fat": nutrients.get("fat"),
        },
        "recipe": meal.get("recipe", {}),
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
        "recent_meals": (meals_payload.get("data") or [])[:8],
        "current_recommendations": [
            _compact_recommendation(meal) for meal in (recommendations or [])[:6]
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
    logged = progress.get("calories", {}).get("total", 0) if isinstance(progress, dict) else 0
    return (
        f"My first pick is {first['meal']}. It has about {calories} calories and {protein}g protein. "
        f"You have logged about {logged} calories today."
    )


def chat_with_model(username, message, history=None, recommendations=None):
    if not username:
        return fail("Username is required.")
    if not message:
        return fail("Message is required.")

    context = _context(username, recommendations or [])
    progress = context.get("today_progress") or {}
    if not OPENAI_API_KEY:
        return ok(
            "OpenAI API key is not configured; using local fallback chat.",
            {
                "reply": _fallback_reply(message, recommendations or [], progress),
                "model": "local-fallback",
            },
        )

    input_items = [
        {
            "role": "developer",
            "content": (
                "You are Ctrl+Eat's recommendation coach. Use the provided user context, "
                "meal log, goals, preferences, and recommendation cards to have a helpful "
                "conversation. Be concise, practical, and clear. Do not claim to diagnose, "
                "treat, or provide medical advice. If asked for a recipe, use the recipe "
                "and ingredient data in context first."
            ),
        },
        {
            "role": "user",
            "content": "User context JSON:\n" + json.dumps(context, default=str),
        },
    ]

    for item in (history or [])[-8:]:
        role = "assistant" if item.get("role") == "assistant" else "user"
        input_items.append({"role": role, "content": item.get("text", "")})
    input_items.append({"role": "user", "content": message})

    body = json.dumps(
        {
            "model": OPENAI_MODEL,
            "input": input_items,
            "max_output_tokens": 450,
            "store": False,
            "truncation": "auto",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return fail(f"OpenAI chat request failed: {detail}", 502)
    except (urllib.error.URLError, TimeoutError) as error:
        return fail(f"OpenAI chat request failed: {error}", 502)

    reply = _extract_text(payload)
    if not reply:
        return fail("OpenAI returned an empty chat response.", 502)

    return ok(
        "Chat response generated successfully.",
        {
            "reply": reply,
            "model": OPENAI_MODEL,
            "response_id": payload.get("id"),
        },
    )
