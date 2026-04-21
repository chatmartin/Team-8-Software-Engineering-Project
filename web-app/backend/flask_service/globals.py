"""Shared configuration and response helpers for the Flask service."""

import os
from pathlib import Path

from flask import g
import psycopg2


def _load_env_file(path):
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _load_project_env():
    project_root = Path(__file__).resolve().parents[2]
    _load_env_file(project_root / ".env.local")
    _load_env_file(project_root / ".env")


_load_project_env()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_SSLMODE = os.getenv("POSTGRES_SSLMODE", "require")
ADMIN_BOOTSTRAP_USERNAMES = {
    username.strip().lower()
    for username in os.getenv("ADMIN_BOOTSTRAP_USERNAMES", "").split(",")
    if username.strip()
}

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

VALID_DIETS = [
    "glutenFree",
    "ketogenic",
    "vegetarian",
    "vegan",
    "pescetarian",
    "paleo",
    "primal",
    "whole30",
]
VALID_ALLERGENS = [
    "dairy",
    "egg",
    "gluten",
    "grain",
    "peanut",
    "seafood",
    "sesame",
    "shellfish",
    "soy",
    "sulfite",
    "tree nut",
    "wheat",
]
CUSTOM_RESTRICTION_EXCLUDES = {
    "halal": ["pork", "alcohol", "blood"],
    "kosher": [
        "pork",
        "shellfish",
        "squid",
        "octopus",
        "shark",
        "eel",
        "insects",
        "blood",
        "rabbit",
        "camel",
    ],
    "beef free": ["beef"],
    "dairy free": ["dairy"],
    "egg free": ["egg"],
}


def api_response(success, message, data=None, status=200):
    return {"success": success, "message": message, "data": data}, status


def ok(message="Success.", data=None, status=200):
    return api_response(True, message, data, status)


def fail(message, status=400, data=None):
    return api_response(False, message, data, status)


def get_db_conn():
    if not DB_HOST or not DB_USER or not DB_PASSWORD:
        return None
    if "db" not in g:
        g.db = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode=DB_SSLMODE,
            connect_timeout=10,
        )
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
