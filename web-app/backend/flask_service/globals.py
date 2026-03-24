#this file is meant for holding global variables
from urllib.parse import quote_plus
from flask import g
import psycopg2

database_password = "&#NqS13N09@D9J" #database password
encoded_pw = quote_plus(database_password)
spoon_api_key = "c2c71fa258d949ec88a299c50b79334b"

def get_db_conn():
    if 'db' not in g:
        g.db = psycopg2.connect(
            host="aws-1-us-east-1.pooler.supabase.com",
            dbname="postgres",
            user="postgres.ezhtwxsfnfplbynavqtr",
            password=database_password,
            port=5432
        )#establishes connection with the database
    return g.db