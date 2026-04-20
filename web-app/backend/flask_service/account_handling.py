import string

from email_validator import EmailNotValidError, validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from .globals import fail, get_db_conn, ok


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


def create_account(username, password, email_addr=None):
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
        query = "INSERT INTO login_info(username,password,email_address) VALUES(%s,%s,%s)"
        cursor.execute(query, (username, hash_pw(password), email_addr))
        conn.commit()
    return ok("Account created successfully.", {"username": username}, 201)


def login(username, password):
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
            return ok("Login successful.", {"username": username})
        return fail("Invalid username or password.", 401)


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
