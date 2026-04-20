from flask_service.account_handling import check_pw
from flask_service.globals import fail, ok


def test_pw_check_requires_length_digit_uppercase_and_symbol():
    assert not check_pw("weakpassword")
    assert not check_pw("Am3)")
    assert not check_pw("lowercase123!")
    assert check_pw("123ABC@$&longer")


def test_response_helpers_use_standard_shape():
    payload, status = ok("Saved.", {"id": 1}, 201)
    assert status == 201
    assert payload == {"success": True, "message": "Saved.", "data": {"id": 1}}

    payload, status = fail("Nope.", 404)
    assert status == 404
    assert payload == {"success": False, "message": "Nope.", "data": None}
