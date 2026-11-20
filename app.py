
import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from keyserv import KEYS

app = Flask(__name__)


def parse_expiry(value):
    return datetime.strptime(
        value, "%Y-%m-%d %H:%M"
    ).replace(tzinfo=timezone.utc)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "server": "HAMA KEY SERVER",
        "status": "online",
        "version": "3.0"
    })


@app.route("/check", methods=["POST"])
def check_key():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "")

    if not isinstance(key, str) or not key:
        return jsonify({
            "valid": False,
            "reason": "invalid_key"
        }), 400

    expiry_text = KEYS.get(key)

    if not expiry_text:
        return jsonify({
            "valid": False,
            "reason": "invalid_key"
        }), 403

    try:
        expiry = parse_expiry(expiry_text)
    except ValueError:
        return jsonify({
            "valid": False,
            "reason": "invalid_expiry"
        }), 500

    now = datetime.now(timezone.utc)

    if now >= expiry:
        return jsonify({
            "valid": False,
            "reason": "expired"
        }), 403

    return jsonify({
        "valid": True,
        "expires": expiry_text
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
