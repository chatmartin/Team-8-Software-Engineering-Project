import string

from email_validator import EmailNotValidError, validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from .globals import get_db_conn


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
        valid_email = validate_email(email, check_deliverability=True).normalized
    except EmailNotValidError:
        return None
    return valid_email


def create_account(username, password, email_addr=None):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    if not check_pw(password):
        return "ERROR: Invalid password."
    if email_addr is not None and not verify_email(email_addr):
        return "ERROR: Email address is invalid."
    with conn.cursor() as cursor:
        query = "SELECT * FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        if cursor.fetchone():
            return "ERROR: Account already exists."
        query = "INSERT INTO login_info(username,password,email_address) VALUES(%s,%s,%s)"
        cursor.execute(query, (username, hash_pw(password), email_addr))
        conn.commit()
    return "Account created successfully."


def login(username, password):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    query = "SELECT password FROM login_info WHERE username = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if not row:
            return "ERROR: Invalid username or password."
        if check_password_hash(row[0], password):
            return "Login successful."
        return "ERROR: Invalid username or password."


def update_email(username, email_addr):
    conn = get_db_conn()
    if conn is None:
        return "ERROR: Unable to access database."
    if email_addr is None:
        return "ERROR: No email address provided."
    if not verify_email(email_addr):
        return "ERROR: Email address is invalid."
    query = "UPDATE login_info SET email_address = %s WHERE username = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (email_addr, username))
        conn.commit()
        if cursor.rowcount == 0:
            return "ERROR: User not found."
    return "Email address updated successfully."
