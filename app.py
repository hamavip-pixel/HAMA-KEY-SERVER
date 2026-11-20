
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

app = Flask(__name__)

# Temporary storage for testing
keys = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "server": "HAMA KEY SERVER",
        "status": "online",
        "version": "1.0"
    })

@app.route("/create", methods=["POST"])
def create_key():
    data = request.get_json(silent=True) or {}
    days = data.get("days", 30)

    if not isinstance(days, int) or isinstance(days, bool):
        return jsonify({"error": "Invalid days"}), 400

    if days < 1 or days > 365:
        return jsonify({"error": "Days must be 1-365"}), 400

    key = "HAMA-" + token_urlsafe(18)
    expires = datetime.now(timezone.utc) + timedelta(days=days)

    keys[key] = {
        "expires": expires.isoformat(),
        "active": True
    }

    return jsonify({
        "key": key,
        "expires": expires.isoformat(),
        "days": days
    })

@app.route("/check", methods=["POST"])
def check_key():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "")
    record = keys.get(key)

    if not record or not record["active"]:
        return jsonify({"valid": False}), 403

    expires = datetime.fromisoformat(record["expires"])

    if datetime.now(timezone.utc) >= expires:
        return jsonify({
            "valid": False,
            "reason": "expired"
        }), 403

    return jsonify({
        "valid": True,
        "expires": record["expires"]
    })

if __name__ == "__main__":
    app.run()
