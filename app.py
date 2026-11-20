
import os
import sqlite3
import secrets
import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = os.getenv("DATABASE_PATH", "hama_keys.db")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                license_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        supplied = request.headers.get("X-Admin-Key", "")

        if not ADMIN_SECRET or not hmac.compare_digest(
            supplied, ADMIN_SECRET
        ):
            return jsonify({"error": "Unauthorized"}), 401

        return func(*args, **kwargs)

    return wrapper


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "server": "HAMA KEY SERVER",
        "status": "online",
        "version": "2.0"
    })


@app.route("/create", methods=["POST"])
@admin_required
def create_key():
    data = request.get_json(silent=True) or {}
    days = data.get("days", 30)

    if not isinstance(days, int) or isinstance(days, bool):
        return jsonify({"error": "Invalid days"}), 400

    if days not in [1, 7, 30, 365]:
        return jsonify({"error": "Allowed: 1, 7, 30, 365 days"}), 400

    key = "HAMA-" + secrets.token_urlsafe(24)

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)

    with get_db() as db:
        db.execute("""
            INSERT INTO licenses
            (license_key, created_at, expires_at, active)
            VALUES (?, ?, ?, 1)
        """, (key, now.isoformat(), expires.isoformat()))

    return jsonify({
        "success": True,
        "key": key,
        "days": days,
        "expires": expires.isoformat()
    })


@app.route("/check", methods=["POST"])
def check_key():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "")

    if not isinstance(key, str) or not key:
        return jsonify({"valid": False}), 400

    with get_db() as db:
        record = db.execute(
            "SELECT * FROM licenses WHERE license_key = ?",
            (key,)
        ).fetchone()

    if not record or not record["active"]:
        return jsonify({"valid": False}), 403

    expires = datetime.fromisoformat(record["expires_at"])

    if datetime.now(timezone.utc) >= expires:
        return jsonify({
            "valid": False,
            "reason": "expired"
        }), 403

    return jsonify({
        "valid": True,
        "expires": record["expires_at"]
    })


@app.route("/deactivate", methods=["POST"])
@admin_required
def deactivate_key():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "")

    if not isinstance(key, str) or not key:
        return jsonify({"error": "Invalid key"}), 400

    with get_db() as db:
        result = db.execute(
            "UPDATE licenses SET active = 0 WHERE license_key = ?",
            (key,)
        )

    if result.rowcount == 0:
        return jsonify({"error": "Key not found"}), 404

    return jsonify({
        "success": True,
        "message": "Key deactivated"
    })


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
