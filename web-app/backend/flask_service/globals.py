"""Shared configuration and response helpers for the Flask service."""

import os

from flask import g
import psycopg2


DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

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
        )
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
