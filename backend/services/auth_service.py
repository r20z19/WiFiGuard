import hashlib
import jwt
from datetime import datetime, timedelta, timezone

from database import get_db

SECRET_KEY = "wifiguard-secret-key-2026-change-in-production"
TOKEN_EXPIRE_HOURS = 24


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _generate_token(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def authenticate_user(username, password):
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, password_hash, is_first_login FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()

    if not user:
        return None

    if user["password_hash"] != _hash_password(password):
        return None

    token = _generate_token(user["id"], user["username"])
    return {
        "token": token,
        "isFirstLogin": bool(user["is_first_login"]),
    }


def verify_user_token(token):
    payload = verify_token(token)
    if not payload:
        return None

    conn = get_db()
    user = conn.execute(
        "SELECT id, username, is_first_login FROM users WHERE id = ?",
        (payload["user_id"],),
    ).fetchone()
    conn.close()

    if not user:
        return None

    return {
        "valid": True,
        "username": user["username"],
        "isFirstLogin": bool(user["is_first_login"]),
    }


def change_user_password(token, old_password, new_password):
    payload = verify_token(token)
    if not payload:
        return False, "无效令牌"

    conn = get_db()
    user = conn.execute(
        "SELECT id, password_hash FROM users WHERE id = ?",
        (payload["user_id"],),
    ).fetchone()

    if not user:
        conn.close()
        return False, "用户不存在"

    if user["password_hash"] != _hash_password(old_password):
        conn.close()
        return False, "旧密码错误"

    conn.execute(
        "UPDATE users SET password_hash = ?, is_first_login = 0 WHERE id = ?",
        (_hash_password(new_password), user["id"]),
    )
    conn.commit()
    conn.close()
    return True, "密码修改成功"
