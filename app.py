"""Entry point. Wires the boundary layer (Flask blueprints) into one app."""
import os

from flask import Flask, render_template

from boundary import (account_boundary, analytics_boundary, auth_boundary, company_boundary,
                      favourite_boundary, idp_boundary, platform_boundary, portfolio_boundary)
from boundary.api import chat_api
from boundary.llm_gateway import LLMGateway
from entity import db, storage

BLUEPRINTS = (auth_boundary, account_boundary, company_boundary, idp_boundary, portfolio_boundary,
              favourite_boundary, analytics_boundary, platform_boundary)


def create_app(db_path=None, upload_dir=None, llm_gateway=None, chat_rate_limit=20):
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
    for module in BLUEPRINTS:
        app.register_blueprint(module.bp)
    app.register_blueprint(portfolio_boundary.api_bp)
    app.register_blueprint(chat_api.bp)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="Sorry, that page doesn't exist."), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", message="That file is too large. Images must be 5 MB or smaller."), 413

    return app


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
