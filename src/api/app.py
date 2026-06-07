"""Flask application factory — with WebSocket (flask-sock) support."""

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from api.config import API_PREFIX, DEBUG, HOST, PORT
from api.database import close_db
from api.routes.predict   import predict_bp
from api.routes.plants    import plants_bp
from api.routes.diseases  import diseases_bp
from api.routes.auth      import auth_bp
from api.routes.realtime_ws import sock   # ← WebSocket Sock instance


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    # ── CORS ─────────────────────────────────────────────────────
    CORS(app)

    # ── flask-sock (WebSocket) ────────────────────────────────────
    # Must call init_app BEFORE the @sock.route decorators are executed,
    # i.e. after importing the module that holds them.
    sock.init_app(app)

    # ── Swagger / OpenAPI ─────────────────────────────────────────
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint":     "apispec",
                "route":        "/apispec.json",
                "rule_filter":  lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui":      True,
        "specs_route":     "/api/docs",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title":       "Plant Disease Detection API",
            "description": (
                "REST API for plant disease detection with MongoDB storage. "
                "Real-time detection via WebSocket at ws://<host>/ws/predict."
            ),
            "version": "0.3.0",
        },
        "host":     f"{HOST}:{PORT}",
        "basePath": "/",
        "schemes":  ["http", "ws"],
        "consumes": ["application/json", "multipart/form-data"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "BearerAuth": {
                "type":        "apiKey",
                "name":        "Authorization",
                "in":          "header",
                "description": "Enter: **Bearer &lt;token&gt;**",
            }
        },
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # ── Blueprints ────────────────────────────────────────────────
    app.register_blueprint(auth_bp,     url_prefix=API_PREFIX)
    app.register_blueprint(predict_bp,  url_prefix=API_PREFIX)
    app.register_blueprint(plants_bp,   url_prefix=API_PREFIX)
    app.register_blueprint(diseases_bp, url_prefix=API_PREFIX)
    # Note: WebSocket route /ws/predict is registered via sock.init_app above.

    # ── Health check ──────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy", "service": "plant-disease-api"}), 200

    # ── Root ──────────────────────────────────────────────────────
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "service": "Plant Disease Detection API",
            "version": "0.3.0",
            "endpoints": {
                "health":        "/health",
                "docs":          "/api/docs",
                "register":      f"{API_PREFIX}/auth/register",
                "login":         f"{API_PREFIX}/auth/login",
                "me":            f"{API_PREFIX}/auth/me",
                "predict":       f"{API_PREFIX}/predict",       # HTTP (single image)
                "predict_ws":    "ws://<host>/ws/predict",      # WebSocket (realtime)
                "plants":        f"{API_PREFIX}/plants",
                "diseases":      f"{API_PREFIX}/diseases",
                "admin":         f"{API_PREFIX}/admin/users",
            },
        }), 200

    # ── Error handlers ────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # ── Cleanup ───────────────────────────────────────────────────
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_db()

    return app


def main():
    """
    Run development server.

    flask-sock requires a WSGI server that supports WebSockets.
    For development: use the built-in server (werkzeug supports WS).
    For production : use gevent or gunicorn+geventwebsocket.

      pip install gunicorn gevent geventwebsocket
      gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \\
               -w 1 "api.app:create_app()"
    """
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()