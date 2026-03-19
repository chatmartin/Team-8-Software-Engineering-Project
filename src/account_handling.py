#this file is meant for holding the functions that will handle account creations and logins
from globals import *
import string

cursor = get_db_conn().cursor()

def check_username(username): #checks if the username is valid (specifically, not taken by another user)
    if cursor is None: #false if we cannot access database
        return False
    query = "SELECT " + username + " FROM login-info"
    cursor.execute(query)
    return cursor.fetchone() is None  #This is true if the username is not found in the database -> username is not taken

#TODO: set requirements for password (e.g., length, characters, etc.) for extra security, may need to edit to account for different cases to tell user what to change
def check_pw(password): #if database is not connected, return false
    if cursor is None: #false if we cannot access database
        return False
    if len(password)<12 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password) or not any(char in string.punctuation for char in password):
        return False
    return True

#TODO: encrypt password for extra security. hash MUST return unique and consistent values for each unique input string
def hash_pw(password):
    return password

def create_account(username,password,email_addr=None):
    if cursor is None: #if database is not connected, give an error
        return "ERROR: Unable to access database."
    if not check_pw(password): #check that password is valid
        return "ERROR: Invalid password."
    if not check_username(username): #check that username is not taken
        return "ERROR: Username is taken."
    query = "INSERT INTO login-info(username,password,email_address) VALUES("+username+","+hash_pw(password)+","+email_addr+")" #make sure to store hashed password
    cursor.execute(query)
    return "Account created successfully."

def login(username,password):
    if cursor is None: #if database is not connected, give an error
        return "ERROR: Unable to access database."
    query = "SELECT " + password + " FROM login-info WHERE username = " + username
    cursor.execute(query)
    if hash_pw(password) == cursor.fetchone(): #make sure to compare hashed password to the stored password
        return "Login successful."
    else: #passwords don't match -> error
        return "ERROR: Invalid username or password."
