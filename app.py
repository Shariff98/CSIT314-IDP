"""Entry point. Wires the boundary layer (Flask blueprints) into one app."""
import os

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from boundary import (account_boundary, analytics_boundary, auth_boundary, company_boundary,
                      favourite_boundary, idp_boundary, platform_boundary, portfolio_boundary)
from boundary.api import chat_api
from boundary.llm_gateway import LLMGateway
from entity import db, storage

BLUEPRINTS = (auth_boundary, account_boundary, company_boundary, idp_boundary, portfolio_boundary,
              favourite_boundary, analytics_boundary, platform_boundary)
# JSON API blueprints used by the React app (each sits in the same module as its HTML pages).
API_BLUEPRINTS = (portfolio_boundary.api_bp, company_boundary.api_bp, analytics_boundary.api_bp, chat_api.bp)


def create_app(db_path=None, upload_dir=None, llm_gateway=None, chat_rate_limit=20, frontend_dist=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["LLM_GATEWAY"] = llm_gateway or LLMGateway()   # budget chatbot (boundary to the LLM service)
    app.config["CHAT_RATE_LIMIT"] = chat_rate_limit
    app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024          # uploads are limited to 5 MB per image
    app.config["UPLOAD_FOLDER"] = os.path.abspath(
        upload_dir or os.environ.get("UPLOAD_DIR", os.path.join(app.root_path, "uploads")))
    db.configure(db_path or os.environ.get("DB_PATH", os.path.join(app.root_path, "platform.db")))
    storage.configure(app.config["UPLOAD_FOLDER"])
    db.init_db()
    app.config["REACT_APP"] = _serve_react(app, frontend_dist or os.environ.get("FRONTEND_DIST"))
    for module in BLUEPRINTS:
        app.register_blueprint(module.bp)
    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)
    _register_error_pages(app)
    return app


def _wants_json():
    return request.path.startswith("/api/")


def _register_error_pages(app):
    """HTML error pages for the Jinja pages; the same errors as JSON for /api/, so React always
    gets {"error": {"code", "message"}} instead of an HTML page it can't read."""
    def error(code, message, status):
        if _wants_json():
            return jsonify(error={"code": code, "message": message}), status
        return render_template("error.html", message=message), status

    @app.errorhandler(404)
    def not_found(_error):
        return error("not_found", "Sorry, that page doesn't exist.", 404)

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return error("method_not_allowed", "That action isn't allowed here.", 405) if _wants_json() else exc

    @app.errorhandler(413)
    def too_large(_error):
        return error("too_large", "That file is too large. Images must be 5 MB or smaller.", 413)

    @app.errorhandler(500)
    def server_error(exc):
        return error("server_error", "Something went wrong on the server. Please try again.", 500) \
            if _wants_json() else exc


def _serve_react(app, dist):
    """In production, serve the built React app (npm run build) from the same address as /api.

    Off unless FRONTEND_DIST points at a folder containing index.html, so local development
    (Vite on :5173) and the tests are unchanged. Registered before the blueprints so that
    "/" shows the React app instead of the old HTML home page. Returns True when it is on.
    """
    if not dist or not os.path.isfile(os.path.join(dist, "index.html")):
        return False
    dist = os.path.abspath(dist)

    @app.get("/")
    def react_index():
        return send_from_directory(dist, "index.html")

    @app.get("/<path:name>")
    def react_file(name):  # assets/, project-kitchen.svg, favicon, ...
        if not os.path.isfile(os.path.join(dist, name)):
            abort(404)
        return send_from_directory(dist, name)

    return True


def _load_dotenv(path=".env"):
    """Reads KEY=value lines from .env (LLM_API_KEY etc.) so you don't need an extra package."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))


if __name__ == "__main__":
    _load_dotenv()
    create_app().run(debug=True)
