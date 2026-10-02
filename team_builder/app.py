from __future__ import annotations

from flask import Flask, flash, jsonify, redirect, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from team_builder import __version__, api, web
from team_builder.config import Config, check_config

csrf = CSRFProtect()

CSP = (
    "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
    "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
)


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    check_config(app.config)

    csrf.init_app(app)
    app.register_blueprint(web.bp)
    app.register_blueprint(api.bp)
    csrf.exempt(api.bp)  # token-less JSON API; no cookies are used for auth

    @app.context_processor
    def inject_version():
        return {"app_version": __version__}

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.errorhandler(413)
    def too_large(_):
        limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        if request.path.startswith("/api/"):
            return jsonify({"error": f"Request is larger than {limit} MB."}), 413
        flash(f"That file is larger than {limit} MB.", "error")
        return redirect(url_for("web.index"))

    @app.errorhandler(CSRFError)
    def csrf_failed(_):
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("web.index"))

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found."}), 404
        return redirect(url_for("web.index"))

    return app
