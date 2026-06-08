"""Flask application factory — production ready (Render + Gunicorn)."""

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from api.config import API_PREFIX, DEBUG, HOST, PORT
from api.database import close_db

from api.routes.predict import predict_bp
from api.routes.plants import plants_bp
from api.routes.diseases import diseases_bp
from api.routes.auth import auth_bp
from api.routes.realtime_ws import sock


def create_app():
    app = Flask(__name__)

    # ── CORS ─────────────────────────────
    CORS(app)

    # ── WebSocket ─────────────────────────
    sock.init_app(app)

    # ── Swagger ───────────────────────────
    swagger_config = {
        "headers": [],
        "specs": [{
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Plant Disease Detection API",
            "version": "0.3.0",
        },
        "basePath": "/",
        "schemes": ["http", "ws"],
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # ── Blueprints ─────────────────────────
    app.register_blueprint(auth_bp, url_prefix=API_PREFIX)
    app.register_blueprint(predict_bp, url_prefix=API_PREFIX)
    app.register_blueprint(plants_bp, url_prefix=API_PREFIX)
    app.register_blueprint(diseases_bp, url_prefix=API_PREFIX)

    # ── Health ─────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
