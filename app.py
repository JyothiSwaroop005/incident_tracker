"""Application entrypoint.

Run locally with:
    python app.py
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask
from flask_wtf import CSRFProtect

from config import Config
from models import db


def create_app(config_class: type = Config) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CSRFProtect(app)

    from routes import bp as incidents_bp
    app.register_blueprint(incidents_bp)

    @app.context_processor
    def inject_globals():
        """Make common values available to every template."""
        return {"current_year": datetime.now(timezone.utc).year}

    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template
        return render_template("404.html"), 404

    with app.app_context():
        db.create_all()
        _seed_if_empty()

    return app


def _seed_if_empty() -> None:
    """Insert a handful of demo incidents on first run so the dashboard
    isn't empty the moment someone opens it."""
    from models import Incident

    if db.session.scalar(db.select(Incident.id)) is not None:
        return

    demo_incidents = [
        Incident(
            title="API latency spike in us-east-1",
            description="p99 latency up 4x on the /checkout endpoint. Suspected connection pool exhaustion on the payments service.",
            severity="critical",
            status="investigating",
            reported_by="Priya Nair",
            assigned_to="SRE On-call",
        ),
        Incident(
            title="DynamoDB throttling on Orders table",
            description="WriteThrottleEvents alarm firing intermittently during peak hours. Likely under-provisioned write capacity.",
            severity="high",
            status="open",
            reported_by="Automated Alert",
            assigned_to="Platform Team",
        ),
        Incident(
            title="Stale CloudWatch dashboard widget",
            description="Widget shows cached data instead of live metrics. Cosmetic issue only, no customer impact.",
            severity="low",
            status="resolved",
            reported_by="Dev Team",
            assigned_to="Priya Nair",
        ),
        Incident(
            title="Elevated 5xx errors on auth service",
            description="Intermittent 502s from the auth service after last night's deploy. Rollback in progress.",
            severity="high",
            status="investigating",
            reported_by="Automated Alert",
            assigned_to="SRE On-call",
        ),
        Incident(
            title="SSL certificate expiring in 5 days",
            description="Certificate for api.example.com expires soon. Needs renewal before it lapses.",
            severity="medium",
            status="open",
            reported_by="Security Bot",
            assigned_to=None,
        ),
    ]
    db.session.bulk_save_objects(demo_incidents)
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
