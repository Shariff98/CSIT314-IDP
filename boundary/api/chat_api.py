"""Boundary (API): POST /api/chat, called by the React ChatWidget.

Request:  {"message": "modern kitchen around $10k", "history": [{"role": "user", "content": "..."}],
           "context": <the "prefs" from the previous response, optional>}
Response: 200 {"reply": str, "projects": [card, ...], "relaxed": [str], "source": "llm" | "fallback",
               "prefs": {"budget", "budget_min", "category", "styles", "exclude_styles", "property_type",
                         "location", "strict_max", "seen_ids"},
               "suggestions": [str]}  follow-up chips; each is a message the bot understands
          400 {"error": str}  empty or too long message
          429 {"error": str}  more than CHAT_RATE_LIMIT messages in an hour

GET /api/chat/status[?check=1]: {"configured", "provider", "model", "fallback_model", "last_call", "check"}
"""
from flask import Blueprint, current_app, jsonify, request, session

from control.rate_limiter import RateLimiter
from control.recommend_idps_controller import RecommendIDPsController

bp = Blueprint("chat_api", __name__, url_prefix="/api")
MAX_MESSAGE_LENGTH = 500


def _limiter():
    if "CHAT_LIMITER" not in current_app.extensions:
        current_app.extensions["CHAT_LIMITER"] = RateLimiter(limit=current_app.config.get("CHAT_RATE_LIMIT", 20))
    return current_app.extensions["CHAT_LIMITER"]


@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="Please type a message."), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(error=f"Please keep your message under {MAX_MESSAGE_LENGTH} characters."), 400
    history = data.get("history") if isinstance(data.get("history"), list) else []
    context = data.get("context") if isinstance(data.get("context"), dict) else None

    user_id = session.get("user_id")
    client = f"user:{user_id}" if user_id else f"ip:{request.headers.get('X-Forwarded-For', request.remote_addr)}"
    if not _limiter().allow(client):
        return jsonify(error="You've sent a lot of messages. Please try again in a while."), 429

    controller = RecommendIDPsController(current_app.config["LLM_GATEWAY"])
    try:
        result = controller.recommend(message, history, customer_id=user_id, context=context)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result)


@bp.get("/chat/status")
def chat_status():
    """Is the AI service really being used? Shows whether a key is set (never the key), the model,
    and how the last call went. ?check=1 also makes one tiny live request (counts against the
    same rate limit as chat messages). Open it on Render after setting LLM_API_KEY."""
    gateway = current_app.config["LLM_GATEWAY"]
    status = gateway.status() if hasattr(gateway, "status") else {"configured": None}
    if request.args.get("check") == "1" and hasattr(gateway, "ping"):
        client = f"ip:{request.headers.get('X-Forwarded-For', request.remote_addr)}"
        if not _limiter().allow(client):
            return jsonify(error="Too many checks. Please try again in a while."), 429
        status["check"] = gateway.ping()
        status["last_call"] = gateway.status().get("last_call")
    return jsonify(status)
