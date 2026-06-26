from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from chatbot import FAQChatbot, load_faqs
import logging
import os
import json

# ---------------------------------
# App Setup
# ---------------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/chat": {"origins": "*"}})

# Load chatbot
faqs = load_faqs()
bot = FAQChatbot(faqs)


# ---------------------------------
# Routes
# ---------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.post("/chat")
def chat():
    """Main chatbot route used by the frontend."""
    try:
        data = request.get_json() or {}
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return jsonify({
                "reply": "Please type a question.",
                "source": "System",
                "score": 0
            }), 400

        reply, source, score = bot.answer(user_message)

        return jsonify({
            "reply": reply,
            "source": source,
            "score": float(score)
        })

    except Exception as e:
        app.logger.exception("Chatbot Error")
        return jsonify({
            "reply": "⚠️ Server error — please try again later.",
            "source": "System",
            "score": 0
        }), 500


# ---------------------------------
# Admin Panel + CRUD for FAQs
# ---------------------------------

FAQ_FILE = "faqs.json"

def read_faqs():
    try:
        with open(FAQ_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def write_faqs(data):
    with open(FAQ_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/admin")
def admin_panel():
    return render_template("admin.html")


@app.get("/api/faqs")
def get_faqs():
    return jsonify(read_faqs())


@app.post("/api/faqs")
def add_faq():
    faqs = read_faqs()
    faqs.append(request.json)
    write_faqs(faqs)
    return jsonify({"status": "added"})


@app.put("/api/faqs/<int:index>")
def update_faq(index):
    faqs = read_faqs()
    if index < 0 or index >= len(faqs):
        return jsonify({"error": "Invalid index"}), 400

    faqs[index] = request.json
    write_faqs(faqs)
    return jsonify({"status": "updated"})


@app.delete("/api/faqs/<int:index>")
def delete_faq(index):
    faqs = read_faqs()
    if index < 0 or index >= len(faqs):
        return jsonify({"error": "Invalid index"}), 400

    faqs.pop(index)
    write_faqs(faqs)
    return jsonify({"status": "deleted"})


# ---------------------------------
# App Runner
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
