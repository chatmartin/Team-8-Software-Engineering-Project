"""Gemini API helpers for Ctrl+Eat AI features."""

import json
import re
import urllib.error
import urllib.request

from .globals import GEMINI_API_KEY, GEMINI_MODEL


class GeminiError(Exception):
    pass


def _error_message(detail):
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return detail[:500]
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or "Gemini request failed."
        status = error.get("status")
        code = error.get("code")
        parts = [message]
        if status:
            parts.append(f"status={status}")
        if code:
            parts.append(f"code={code}")
        return " ".join(parts)
    return detail[:500]


def _extract_text(payload):
    chunks = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if part.get("text"):
                chunks.append(part["text"])
    return "\n".join(chunks).strip()


def _content(role, text):
    return {"role": role, "parts": [{"text": text}]}


def generate_text(system_instruction, user_messages, *, temperature=0.4, max_tokens=450):
    if not GEMINI_API_KEY:
        raise GeminiError("Gemini API key is not configured.")

    contents = [_content(role, text) for role, text in user_messages]
    body = json.dumps(
        {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.9,
            },
        }
    ).encode("utf-8")
    model = GEMINI_MODEL if GEMINI_MODEL.startswith("models/") else f"models/{GEMINI_MODEL}"
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise GeminiError(_error_message(detail)) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise GeminiError(str(error)) from error

    text = _extract_text(payload)
    if not text:
        raise GeminiError("Gemini returned an empty response.")
    return text, payload


def parse_json_text(text):
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    return json.loads(cleaned)
