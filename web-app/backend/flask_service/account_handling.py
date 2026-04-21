import string

from email_validator import EmailNotValidError, validate_email
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash

from .globals import ADMIN_BOOTSTRAP_USERNAMES, fail, get_db_conn, ok


def check_pw(password):
    if (
        len(password) < 12
        or not any(char.isdigit() for char in password)
        or not any(char.isupper() for char in password)
        or not any(char in string.punctuation for char in password)
    ):
        return False
    return True


def hash_pw(password):
    return generate_password_hash(password)


def verify_email(email):
    try:
        valid_email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return None
    return valid_email


def _bootstrap_role(username):
    if username and username.lower() in ADMIN_BOOTSTRAP_USERNAMES:
        return "admin"
    return "user"


def _sync_bootstrap_admin(cursor, username):
    if _bootstrap_role(username) != "admin":
        return
    cursor.execute(
        "UPDATE login_info SET role = 'admin' WHERE username = %s AND role <> 'admin'",
        (username,),
    )


def get_account(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    with conn.cursor() as cursor:
        _sync_bootstrap_admin(cursor, username)
        cursor.execute(
            "SELECT username, role FROM login_info WHERE username = %s",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return fail("User not found.", 404)
        conn.commit()
    return ok("Current user obtained successfully.", {"username": row[0], "role": row[1]})


def create_account(username, password, email_addr=None):
    try:
        conn = get_db_conn()
        if conn is None:
            return fail("Database is not configured.", 503)
        if not username:
            return fail("Username is required.")
        if not check_pw(password):
            return fail(
                "Password must be at least 12 characters and include a number, uppercase letter, and symbol."
            )
        if email_addr is not None and not verify_email(email_addr):
            return fail("Email address is invalid.")
        with conn.cursor() as cursor:
            query = "SELECT * FROM login_info WHERE username=%s"
            cursor.execute(query, (username,))
            if cursor.fetchone():
                return fail("Account already exists.", 409)
            query = "INSERT INTO login_info(username,password,email_address,role) VALUES(%s,%s,%s,%s)"
            role = _bootstrap_role(username)
            cursor.execute(query, (username, hash_pw(password), email_addr, role))
            conn.commit()
        return ok("Account created successfully.", {"username": username, "role": role}, 201)
    except psycopg2.errors.UndefinedColumn:
        return fail("Database schema is missing the role column. Run the latest backend/schema.sql in Supabase.", 503)
    except psycopg2.OperationalError:
        return fail("Database connection failed. Check Supabase host, port, username, password, and network compatibility.", 503)
    except psycopg2.Error:
        return fail("Database query failed. Check backend logs for the detailed PostgreSQL error.", 503)


def login(username, password):
    try:
        conn = get_db_conn()
        if conn is None:
            return fail("Database is not configured.", 503)
        query = "SELECT password FROM login_info WHERE username = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if not row:
                return fail("Invalid username or password.", 401)
            if check_password_hash(row[0], password):
                _sync_bootstrap_admin(cursor, username)
                cursor.execute("SELECT role FROM login_info WHERE username = %s", (username,))
                role = cursor.fetchone()[0]
                conn.commit()
                return ok("Login successful.", {"username": username, "role": role})
            return fail("Invalid username or password.", 401)
    except psycopg2.OperationalError:
        return fail("Database connection failed. Check Supabase host, port, username, password, and network compatibility.", 503)
    except psycopg2.errors.UndefinedTable:
        return fail("Database schema is missing. Run backend/schema.sql in Supabase SQL Editor.", 503)
    except psycopg2.Error:
        return fail("Database query failed. Check backend logs for the detailed PostgreSQL error.", 503)


def update_email(username, email_addr):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    if email_addr is None:
        return fail("No email address provided.")
    if not verify_email(email_addr):
        return fail("Email address is invalid.")
    query = "UPDATE login_info SET email_address = %s WHERE username = %s"
    with conn.cursor() as cursor:
        cursor.execute(query,(email_addr,username,))
        conn.commit()
        if cursor.rowcount == 0: 
            return fail("User not found.", 404)
    return ok("Email address updated successfully.", {"email": email_addr})

def delete_account(username):
    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)
    query = "DELETE FROM login_info WHERE username = %s"
    with conn.cursor() as cursor:
        cursor.execute(query,(username,))
        conn.commit()
        if cursor.rowcount == 0:
            return fail("User not found.", 404)
        return ok("Account deleted successfully.")
