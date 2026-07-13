import hashlib
import os
import jwt
from datetime import datetime, timedelta, timezone

from database import get_db

SECRET_KEY = "wifiguard-secret-key-2026-change-in-production"
TOKEN_EXPIRE_HOURS = 24
PBKDF2_ITERATIONS = 600_000
PBKDF2_PREFIX = "pbkdf2-sha256"


def _hash_password(password):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"${PBKDF2_PREFIX}${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def _verify_password(password, stored_hash):
    if PBKDF2_PREFIX in stored_hash:
        parts = stored_hash.split("$")
        if len(parts) == 5:
            _, _, iterations, salt_hex, hash_hex = parts
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
            return dk.hex() == hash_hex
        return False
    # Legacy SHA-256 (no salt) — backward compatible
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash


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

    if not _verify_password(password, user["password_hash"]):
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


def require_auth(token, require_password_changed=True):
    """Validate JWT token and optionally enforce password-change requirement.

    Returns (payload, error_message).  error is None on success.
    """
    if not token:
        return None, "未授权，请先登录"
    payload = verify_token(token)
    if not payload:
        return None, "令牌无效或已过期"

    if require_password_changed:
        conn = get_db()
        user = conn.execute(
            "SELECT is_first_login FROM users WHERE id = ?",
            (payload["user_id"],),
        ).fetchone()
        conn.close()
        if user and user["is_first_login"]:
            return payload, "首次登录，请先修改默认密码"

    return payload, None


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

    if not _verify_password(old_password, user["password_hash"]):
        conn.close()
        return False, "旧密码错误"

    conn.execute(
        "UPDATE users SET password_hash = ?, is_first_login = 0 WHERE id = ?",
        (_hash_password(new_password), user["id"]),
    )
    conn.commit()
    conn.close()
    return True, "密码修改成功"
