#this file is meant for holding global variables
from urllib.parse import quote_plus
from flask import g
import psycopg2

database_password = "&#NqS13N09@D9J" #database password
encoded_pw = quote_plus(database_password)
spoon_api_key = "c2c71fa258d949ec88a299c50b79334b"

def get_db_conn():
    if 'db' not in g:
        g.db = psycopg2.connect("postgresql://postgres:"+encoded_pw+"@db.ezhtwxsfnfplbynavqtr.supabase.co:5432/postgres")#establishes connection with the database
    return g.db