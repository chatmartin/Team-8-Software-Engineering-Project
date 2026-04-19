#The purpose of this file is to test the functions in account_handling.py

from account_handling import *
from main import create_app

def test_pw_check():
    pw1 = 'weakpassword'
    pw2 = 'Am3)'
    pw3 = '<PASSWORD>'
    pw4 = '123ABC@$&longer'
    assert(not check_pw(pw1) and not check_pw(pw2) and not check_pw(pw3) and check_pw(pw4))

#TODO: Have a consistent test for creation, maybe add account deletion?
def test_acc_creation():
    app = create_app()
    with app.app_context():
        msg = create_account("admin",admin_password)
        assert('already exists' in msg)

def test_acc_login():
    app = create_app()
    with app.app_context():
        #Case 1: Valid
        msg = login("NOTTAKEN","123ABC@$&longer")
        assert('successful' in msg)
        #Case 2: Invalid user
        msg = login("TAKEN","<PASSWORD>")
        assert('ERROR' in msg)
        #Case 3: Invalid password
        msg = login("NOTTAKEN","<PASSWORD>")
        assert('ERROR' in msg)
        msg = login("admin",admin_password)
        assert('success' in msg)


def test_email_update():
    app = create_app()
    with app.app_context():
        #Case 1: Invalid email address
        msg = update_email("NOTTAKEN","hi")
        assert('ERROR' in msg)
        #Case 2: Valid
        msg = update_email("NOTTAKEN","mzuckerberg@fb.com")
        assert('successfully' in msg)
        #Case 3: Invalid account
        msg = update_email("NOTNOTTAKEN","mzuckerberg@fb.com")
        assert('ERROR' in msg)