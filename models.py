"""Database models."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow() -> datetime:
    """Return a timezone-aware current UTC timestamp."""
    return datetime.now(timezone.utc)


class Incident(db.Model):
    """A single tracked incident.

    Mirrors the fields used by the original serverless (Lambda/DynamoDB)
    version, plus `reported_by` / `assigned_to` to support ownership and
    accountability in the dashboard UI.
    """

    __tablename__ = "incidents"

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(200), nullable=False)
    description: str = db.Column(db.Text, nullable=False, default="")
    severity: str = db.Column(db.String(20), nullable=False, default="medium", index=True)
    status: str = db.Column(db.String(20), nullable=False, default="open", index=True)
    reported_by: str = db.Column(db.String(120), nullable=False, default="Anonymous")
    assigned_to: str = db.Column(db.String(120), nullable=True)
    created_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: datetime = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    SEVERITY_WEIGHT = {"critical": 3, "high": 2, "medium": 1, "low": 0}

    @property
    def severity_weight(self) -> int:
        """Numeric weight used for severity-based sorting."""
        return self.SEVERITY_WEIGHT.get(self.severity, 0)

    @property
    def is_resolved(self) -> bool:
        return self.status == "resolved"

    def to_dict(self) -> dict:
        """Serialize the incident for JSON responses (e.g. chart data)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "reported_by": self.reported_by,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Incident {self.id} '{self.title}' [{self.severity}/{self.status}]>"
