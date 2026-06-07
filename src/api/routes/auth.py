"""Authentication routes - Register & Login."""

from datetime import datetime, timedelta
from functools import wraps

import bcrypt
from bson import ObjectId
from flask import Blueprint, jsonify, request, g

from api.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS
from api.database import get_db

# ── PyJWT import مع fallback ─────────────────────────────────────
try:
    import jwt
    def _encode_jwt(payload): return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    def _decode_jwt(token):   return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
except ImportError:
    raise ImportError("Run: uv add PyJWT")

auth_bp = Blueprint("auth", __name__)


# ─── JWT Helpers ─────────────────────────────────────────────────

def _generate_token(user_id: str, role: str) -> str:
    payload = {
        "sub":  user_id,
        "role": role,
        "iat":  datetime.utcnow(),
        "exp":  datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    token = _encode_jwt(payload)
    # PyJWT >= 2.0 returns str, older returns bytes
    return token if isinstance(token, str) else token.decode("utf-8")


def _verify_password(plain: str, stored) -> bool:
    """مقارنة كلمة المرور مع hash - يتعامل مع bytes و Binary و str."""
    try:
        plain_bytes = plain.encode("utf-8")
        # تحويل أي نوع لـ bytes
        if isinstance(stored, (bytes, bytearray)):
            hash_bytes = bytes(stored)
        elif isinstance(stored, str):
            hash_bytes = stored.encode("utf-8")
        else:
            # bson.Binary أو أي نوع آخر
            hash_bytes = bytes(stored)
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception as e:
        print(f"[AUTH] Password verify error: {e}")
        return False


# ─── Auth Decorators ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload  = _decode_jwt(token)
            g.user_id   = payload["sub"]
            g.user_role = payload["role"]
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.user_role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ─── LOGIN ───────────────────────────────────────────────────────

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Login with email and password.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:    { type: string, example: "admin@gmail.com" }
            password: { type: string, example: "admin123" }
    responses:
      200: { description: Login successful }
      401: { description: Invalid credentials }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email    = str(data.get("email",    "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        db   = get_db()
        user = db.users.find_one({"email": email})

        if not user:
            return jsonify({"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة"}), 401

        if not _verify_password(password, user.get("password", "")):
            return jsonify({"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة"}), 401

        if not user.get("is_active", True):
            return jsonify({"error": "الحساب موقوف، تواصل مع المشرف"}), 403

        # ── Update last login ──────────────────────────────────
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        user_id = str(user["_id"])
        role    = user.get("role", "user")
        token   = _generate_token(user_id, role)

        return jsonify({
            "token":   token,
            "user_id": user_id,
            "name":    user.get("name", ""),
            "email":   user.get("email", ""),
            "role":    role,
        }), 200

    except Exception as e:
        print(f"[AUTH] Login error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ─── REGISTER (Admin creates users) ──────────────────────────────

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """
    Register a new user (called by admin).
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name:     { type: string }
            email:    { type: string }
            password: { type: string }
            role:     { type: string, enum: [user, admin], default: user }
    responses:
      201: { description: User created }
      400: { description: Validation error }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    name     = str(data.get("name",     "")).strip()
    email    = str(data.get("email",    "")).strip().lower()
    password = str(data.get("password", "")).strip()
    role     = str(data.get("role",     "user")).strip()

    if not name:     return jsonify({"error": "Name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if role not in ("user", "admin"):
        role = "user"

    try:
        db = get_db()
        if db.users.find_one({"email": email}):
            return jsonify({"error": "البريد الإلكتروني مسجّل مسبقاً"}), 400

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        now    = datetime.utcnow()

        result = db.users.insert_one({
            "name":       name,
            "email":      email,
            "password":   hashed,
            "role":       role,
            "is_active":  True,
            "created_at": now,
            "updated_at": now,
        })

        return jsonify({
            "message":  "تم إنشاء الحساب بنجاح",
            "user_id":  str(result.inserted_id),
            "name":     name,
            "email":    email,
            "role":     role,
        }), 201

    except Exception as e:
        print(f"[AUTH] Register error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ─── GET CURRENT USER ─────────────────────────────────────────────

@auth_bp.route("/auth/me", methods=["GET"])
@login_required
def get_me():
    """
    Get current user info.
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200: { description: User info }
    """
    try:
        db   = get_db()
        user = db.users.find_one({"_id": ObjectId(g.user_id)}, {"password": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
        user["_id"] = str(user["_id"])
        if "created_at" in user: user["created_at"] = user["created_at"].isoformat()
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── ADMIN: List users ────────────────────────────────────────────

@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def list_users():
    """
    [Admin] List all users.
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    responses:
      200: { description: List of users }
    """
    try:
        db    = get_db()
        users = list(db.users.find({}, {"password": 0}))
        for u in users:
            u["_id"] = str(u["_id"])
            for f in ("created_at", "updated_at", "last_login"):
                if f in u: u[f] = u[f].isoformat()
        return jsonify({"users": users, "total": len(users)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── ADMIN: Toggle user ───────────────────────────────────────────

@auth_bp.route("/admin/users/<user_id>/toggle", methods=["PUT"])
@admin_required
def toggle_user(user_id: str):
    """
    [Admin] Toggle user active status.
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    """
    if not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid user ID"}), 400
    try:
        db   = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        new_status = not user.get("is_active", True)
        db.users.update_one({"_id": ObjectId(user_id)},
            {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}})
        return jsonify({"message": "Updated", "is_active": new_status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── ADMIN: Delete user ───────────────────────────────────────────

@auth_bp.route("/admin/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id: str):
    """
    [Admin] Delete a user.
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    """
    if not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid user ID"}), 400
    try:
        db     = get_db()
        result = db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "Deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── أضف هذا في routes/auth.py ──────────────────────────────────

@auth_bp.route("/admin/users/<user_id>/reset-password", methods=["PUT"])
@admin_required
def reset_password(user_id: str):
    """
    [Admin] Reset user password.
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [new_password]
          properties:
            new_password:
              type: string
    responses:
      200: { description: Password reset }
      400: { description: Invalid input }
      404: { description: User not found }
    """
    if not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid user ID"}), 400

    data = request.get_json(silent=True)
    new_password = str(data.get("new_password", "")).strip() if data else ""

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        db   = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed, "updated_at": datetime.utcnow()}}
        )
        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── أضف في routes/auth.py ──────────────────────────────────────

@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    """
    Send password reset instructions (simulated - logs token to console).
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email]
          properties:
            email: { type: string, example: "user@example.com" }
    responses:
      200: { description: Reset instructions sent (or simulated) }
      404: { description: Email not found }
    """
    data  = request.get_json(silent=True)
    email = str(data.get("email", "")).strip().lower() if data else ""

    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    try:
        db   = get_db()
        user = db.users.find_one({"email": email})

        if not user:
            return jsonify({"error": "البريد الإلكتروني غير مسجّل"}), 404

        # ── Generate a reset token (valid 1 hour) ──────────────
        reset_token = _generate_token(str(user["_id"]), "reset")

        # ── In production: send email with reset link ───────────
        # For now: store token and log it
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"reset_token": reset_token, "reset_at": datetime.utcnow()}}
        )

        # TODO: integrate with email service (SendGrid, etc.)
        print(f"\n[RESET TOKEN] Email: {email}")
        print(f"[RESET TOKEN] Token: {reset_token}\n")

        return jsonify({
            "message": "Reset instructions sent",
            "debug_token": reset_token  # Remove in production!
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500