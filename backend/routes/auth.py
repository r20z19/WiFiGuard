from flask import Blueprint, jsonify, request

from services.auth_service import authenticate_user, verify_user_token, change_user_password, register_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400

    result = authenticate_user(username, password)
    if result is None:
        return jsonify({"message": "用户名或密码错误"}), 401

    return jsonify(result)


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400
    if len(username) < 2 or len(username) > 32:
        return jsonify({"message": "用户名长度需在2-32个字符之间"}), 400
    if len(password) < 6:
        return jsonify({"message": "密码长度至少6位"}), 400

    success, result = register_user(username, password)
    if not success:
        return jsonify({"message": result}), 400

    return jsonify(result)


@auth_bp.route("/api/auth/verify", methods=["GET"])
def verify():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"valid": False}), 401

    result = verify_user_token(token)
    if result is None:
        return jsonify({"valid": False}), 401

    return jsonify(result)


@auth_bp.route("/api/auth/change-password", methods=["POST"])
def change_password():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"message": "未授权"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400

    old_password = data.get("oldPassword", "")
    new_password = data.get("newPassword", "")

    if not old_password or not new_password:
        return jsonify({"message": "旧密码和新密码不能为空"}), 400

    success, message = change_user_password(token, old_password, new_password)
    if not success:
        return jsonify({"message": message}), 400

    return jsonify({"message": message})
