"""Admin-only account management helpers."""

import psycopg2

from .account_handling import check_pw, hash_pw
from .globals import fail, get_db_conn, ok


VALID_ROLES = {"user", "admin"}


def _admin_id(cursor, username):
    cursor.execute("SELECT user_id, role FROM login_info WHERE username = %s", (username,))
    row = cursor.fetchone()
    if not row:
        return None, fail("Admin user not found.", 404)
    if row[1] != "admin":
        return None, fail("Admin access is required.", 403)
    return row[0], None


def list_users(admin_username):
    try:
        conn = get_db_conn()
        if conn is None:
            return fail("Database is not configured.", 503)
        with conn.cursor() as cursor:
            _admin_user_id, error = _admin_id(cursor, admin_username)
            if error:
                return error
            cursor.execute(
                """
                SELECT
                    l.user_id,
                    l.username,
                    l.email_address,
                    l.role,
                    l.created_at,
                    COUNT(um.user_id) AS meal_count
                FROM login_info l
                LEFT JOIN user_meals um ON um.user_id = l.user_id
                GROUP BY l.user_id, l.username, l.email_address, l.role, l.created_at
                ORDER BY created_at DESC, username ASC
                """
            )
            users = [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "email_address": row[2],
                    "role": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "meal_count": row[5],
                }
                for row in cursor.fetchall()
            ]
        return ok("Users obtained successfully.", users)
    except psycopg2.errors.UndefinedColumn:
        return fail("Database schema is missing an admin user-list column. Run the latest backend/schema.sql in Supabase.", 503)
    except psycopg2.Error:
        return fail("Database query failed while loading admin users.", 503)


def update_user_role(admin_username, target_username, role):
    if role not in VALID_ROLES:
        return fail("Role must be either user or admin.")
    if not target_username:
        return fail("Target username is required.")

    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)

    with conn.cursor() as cursor:
        _admin_user_id, error = _admin_id(cursor, admin_username)
        if error:
            return error
        cursor.execute(
            "SELECT user_id, username, role FROM login_info WHERE username = %s",
            (target_username,),
        )
        target = cursor.fetchone()
        if not target:
            return fail("Target user not found.", 404)

        target_id, target_username, target_role = target
        if admin_username == target_username and target_role == "admin" and role == "user":
            return fail("Admins cannot demote themselves.", 400)

        if target_role == "admin" and role == "user":
            cursor.execute("SELECT COUNT(*) FROM login_info WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                return fail("Cannot demote the final admin.", 400)

        cursor.execute(
            "UPDATE login_info SET role = %s WHERE user_id = %s",
            (role, target_id),
        )
        conn.commit()

    return ok(
        "User role updated successfully.",
        {"username": target_username, "role": role},
    )


def reset_user_password(admin_username, target_username, password):
    if not target_username:
        return fail("Target username is required.")
    if not check_pw(password):
        return fail(
            "Password must be at least 12 characters and include a number, uppercase letter, and symbol."
        )

    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)

    with conn.cursor() as cursor:
        _admin_user_id, error = _admin_id(cursor, admin_username)
        if error:
            return error
        cursor.execute(
            "UPDATE login_info SET password = %s WHERE username = %s RETURNING username",
            (hash_pw(password), target_username),
        )
        row = cursor.fetchone()
        if not row:
            return fail("Target user not found.", 404)
        conn.commit()

    return ok("User password updated successfully.", {"username": row[0]})


def delete_user(admin_username, target_username):
    if not target_username:
        return fail("Target username is required.")

    conn = get_db_conn()
    if conn is None:
        return fail("Database is not configured.", 503)

    with conn.cursor() as cursor:
        _admin_user_id, error = _admin_id(cursor, admin_username)
        if error:
            return error
        cursor.execute(
            "SELECT user_id, username, role FROM login_info WHERE username = %s",
            (target_username,),
        )
        target = cursor.fetchone()
        if not target:
            return fail("Target user not found.", 404)

        target_id, target_username, target_role = target
        if admin_username == target_username:
            return fail("Admins cannot delete themselves.", 400)

        if target_role == "admin":
            cursor.execute("SELECT COUNT(*) FROM login_info WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                return fail("Cannot delete the final admin.", 400)

        cursor.execute("DELETE FROM login_info WHERE user_id = %s", (target_id,))
        conn.commit()

    return ok("User deleted successfully.", {"username": target_username})
