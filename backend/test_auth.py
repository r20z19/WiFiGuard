"""Test script to verify the full auth flow works correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force fresh database for testing
os.environ["WIFIGUARD_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_auth.db")

# Clean up old test db
if os.path.exists(os.environ["WIFIGUARD_DB"]):
    os.remove(os.environ["WIFIGUARD_DB"])

from database import init_db, get_db
from services.auth_service import (
    _hash_password, _verify_password, authenticate_user,
    change_user_password, SECRET_KEY
)
import jwt
from datetime import datetime, timedelta, timezone

# Step 1: Initialize fresh database
print("=== Step 1: Initialize DB ===")
init_db()

# Check the created user
conn = get_db()
user = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
print(f"User: id={user['id']}, username={user['username']}, is_first_login={user['is_first_login']}")
print(f"Password hash: {user['password_hash'][:80]}...")
conn.close()

# Test password verification directly
print("\n=== Step 2: Test _verify_password directly ===")
result = _verify_password("admin", user["password_hash"])
print(f"_verify_password('admin', hash) = {result}")
result = _verify_password("123123", user["password_hash"])
print(f"_verify_password('123123', hash) = {result}")

# Step 3: Authenticate
print("\n=== Step 3: Login ===")
auth_result = authenticate_user("admin", "admin")
if auth_result:
    print(f"Login SUCCESS: token={auth_result['token'][:30]}..., isFirstLogin={auth_result['isFirstLogin']}")
    token = auth_result["token"]
else:
    print("Login FAILED!")
    sys.exit(1)

# Step 4: Change password
print("\n=== Step 4: Change Password ===")
success, msg = change_user_password(token, "admin", "newpass123")
print(f"Change password result: success={success}, message='{msg}'")

if success:
    # Verify the new password works for login
    print("\n=== Step 5: Verify new password ===")
    auth_result2 = authenticate_user("admin", "newpass123")
    if auth_result2:
        print(f"Login with new password: SUCCESS, isFirstLogin={auth_result2['isFirstLogin']}")
    else:
        print("Login with new password: FAILED!")
else:
    print("\n*** FAILED *** Password change did not succeed!")

# Cleanup
conn = get_db()
conn.close()
if os.path.exists(os.environ["WIFIGUARD_DB"]):
    os.remove(os.environ["WIFIGUARD_DB"])
    print("\nTest DB cleaned up.")
