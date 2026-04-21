import flask_service.admin as admin_module


class FakeCursor:
    def __init__(self, users):
        self.users = users
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return False

    def execute(self, query, params=None):
        normalized = " ".join(query.split())
        if normalized.startswith("SELECT user_id, role FROM login_info WHERE username"):
            username = params[0]
            user = self.users.get(username)
            self.result = (user["user_id"], user["role"]) if user else None
        elif normalized.startswith("SELECT user_id, username, role FROM login_info WHERE username"):
            username = params[0]
            user = self.users.get(username)
            self.result = (user["user_id"], username, user["role"]) if user else None
        elif normalized.startswith("SELECT COUNT(*) FROM login_info WHERE role = 'admin'"):
            self.result = (sum(1 for user in self.users.values() if user["role"] == "admin"),)
        elif normalized.startswith("UPDATE login_info SET role"):
            role, user_id = params
            for user in self.users.values():
                if user["user_id"] == user_id:
                    user["role"] = role
                    break
        elif normalized.startswith("UPDATE login_info SET password"):
            password, username = params
            user = self.users.get(username)
            if user:
                user["password"] = password
                self.result = (username,)
            else:
                self.result = None
        elif normalized.startswith("DELETE FROM login_info WHERE user_id"):
            user_id = params[0]
            for username, user in list(self.users.items()):
                if user["user_id"] == user_id:
                    del self.users[username]
                    break

    def fetchone(self):
        return self.result


class FakeConn:
    def __init__(self, users):
        self.users = users
        self.committed = False

    def cursor(self):
        return FakeCursor(self.users)

    def commit(self):
        self.committed = True


def test_regular_user_cannot_update_roles(monkeypatch):
    conn = FakeConn({"member": {"user_id": 1, "role": "user"}})
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.update_user_role("member", "member", "admin")

    assert status == 403
    assert payload["success"] is False


def test_invalid_role_is_rejected_before_database(monkeypatch):
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: None)

    payload, status = admin_module.update_user_role("admin", "member", "owner")

    assert status == 400
    assert payload["message"] == "Role must be either user or admin."


def test_admin_cannot_demote_self(monkeypatch):
    conn = FakeConn({"admin": {"user_id": 1, "role": "admin"}})
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.update_user_role("admin", "admin", "user")

    assert status == 400
    assert payload["message"] == "Admins cannot demote themselves."
    assert conn.users["admin"]["role"] == "admin"


def test_admin_can_promote_user(monkeypatch):
    conn = FakeConn(
        {
            "admin": {"user_id": 1, "role": "admin"},
            "member": {"user_id": 2, "role": "user"},
        }
    )
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.update_user_role("admin", "member", "admin")

    assert status == 200
    assert payload["data"] == {"username": "member", "role": "admin"}
    assert conn.users["member"]["role"] == "admin"
    assert conn.committed is True


def test_admin_can_reset_user_password(monkeypatch):
    conn = FakeConn(
        {
            "admin": {"user_id": 1, "role": "admin"},
            "member": {"user_id": 2, "role": "user", "password": "old"},
        }
    )
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.reset_user_password(
        "admin",
        "member",
        "NewPassword123!",
    )

    assert status == 200
    assert payload["data"] == {"username": "member"}
    assert conn.users["member"]["password"] != "old"
    assert conn.committed is True


def test_admin_cannot_delete_self(monkeypatch):
    conn = FakeConn({"admin": {"user_id": 1, "role": "admin"}})
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.delete_user("admin", "admin")

    assert status == 400
    assert payload["message"] == "Admins cannot delete themselves."
    assert "admin" in conn.users


def test_admin_can_delete_regular_user(monkeypatch):
    conn = FakeConn(
        {
            "admin": {"user_id": 1, "role": "admin"},
            "member": {"user_id": 2, "role": "user"},
        }
    )
    monkeypatch.setattr(admin_module, "get_db_conn", lambda: conn)

    payload, status = admin_module.delete_user("admin", "member")

    assert status == 200
    assert payload["data"] == {"username": "member"}
    assert "member" not in conn.users
    assert conn.committed is True
