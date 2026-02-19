from flask import Flask, jsonify, request

from core import generate_response

app = Flask(__name__)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history")
    if not message:
        return jsonify({"error": "message is required"}), 400
    try:
        result = generate_response(message, history=history)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
