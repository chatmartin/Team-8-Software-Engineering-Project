#The purpose of this file is to test the functions in account_handling.py

from account_handling import *
from main import create_app

def test_pw_check():
    pw1 = 'weakpassword'
    pw2 = 'Am3)'
    pw3 = '<PASSWORD>'
    pw4 = '123ABC@$&longer'
    assert(not check_pw(pw1) and not check_pw(pw2) and not check_pw(pw3) and check_pw(pw4))

def test_acc_creation():
    app = create_app()
    with app.app_context():
        msg = create_account("NOTTAKEN","123ABC@$&longer")
        assert('Account already exists' in msg)