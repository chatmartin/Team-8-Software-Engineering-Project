#The purpose of this file is to test the functions in account_handling.py

from account_handling import *

def test_pw_check():
    pw1 = 'weakpassword'
    pw2 = 'Am3)'
    pw3 = '<PASSWORD>'
    pw4 = '123ABC@$&longer'
    assert(not check_pw(pw1) and not check_pw(pw2) and not check_pw(pw3) and check_pw(pw4))