"""Test suite for the Flask incident tracker.

Run: pytest tests/ -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from config import Config
from models import Incident, db


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    TESTING = True


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        yield application
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


def test_dashboard_loads(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data


def test_root_redirects_to_dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_incident_list_loads(client):
    resp = client.get("/incidents")
    assert resp.status_code == 200


def test_create_incident_success(client, app):
    resp = client.post(
        "/create",
        data={
            "title": "Test outage",
            "description": "Something broke.",
            "severity": "high",
            "status": "open",
            "reported_by": "Tester",
            "assigned_to": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        incident = db.session.scalar(db.select(Incident).filter_by(title="Test outage"))
        assert incident is not None
        assert incident.severity == "high"


def test_create_incident_missing_title_fails(client):
    resp = client.post(
        "/create",
        data={"title": "", "description": "desc", "severity": "high", "status": "open"},
    )
    assert resp.status_code == 200  # re-renders form with errors
    assert b"required" in resp.data.lower()


def test_create_incident_invalid_severity_fails(client, app):
    resp = client.post(
        "/create",
        data={
            "title": "Invalid Sev Title",
            "description": "desc",
            "severity": "apocalyptic",
            "status": "open",
        },
    )
    assert resp.status_code == 200
    with app.app_context():
        incident = db.session.scalar(db.select(Incident).filter_by(title="Invalid Sev Title"))
        assert incident is None


def test_incident_detail_404_for_missing(client):
    resp = client.get("/incident/99999")
    assert resp.status_code == 404
    assert b"404" in resp.data


def test_edit_incident(client, app):
    with app.app_context():
        incident = Incident(title="Edit me", description="d", severity="low", status="open")
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    resp = client.post(
        f"/edit/{incident_id}",
        data={
            "title": "Edited title",
            "description": "updated desc",
            "severity": "critical",
            "status": "investigating",
            "reported_by": "Tester",
            "assigned_to": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        updated = db.session.get(Incident, incident_id)
        assert updated.title == "Edited title"
        assert updated.severity == "critical"


def test_delete_incident(client, app):
    with app.app_context():
        incident = Incident(title="Delete me", description="d", severity="low", status="open")
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    resp = client.post(f"/delete/{incident_id}", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Incident, incident_id) is None


def test_quick_resolve(client, app):
    with app.app_context():
        incident = Incident(title="Resolve me", description="d", severity="low", status="open")
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    resp = client.post(f"/incident/{incident_id}/quick-resolve", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Incident, incident_id).status == "resolved"


def test_search_filters_results(client, app):
    with app.app_context():
        db.session.add(Incident(title="Unique Zephyr Bug", description="d", severity="low", status="open"))
        db.session.add(Incident(title="Something else", description="d", severity="low", status="open"))
        db.session.commit()

    resp = client.get("/incidents?q=Zephyr")
    assert resp.status_code == 200
    assert b"Unique Zephyr Bug" in resp.data
    assert b"Something else" not in resp.data


def test_severity_filter(client, app):
    with app.app_context():
        db.session.add(Incident(title="Crit one", description="d", severity="critical", status="open"))
        db.session.add(Incident(title="Low one", description="d", severity="low", status="open"))
        db.session.commit()

    resp = client.get("/incidents?severity=critical")
    assert resp.status_code == 200
    assert b"Crit one" in resp.data
    assert b"Low one" not in resp.data


def test_status_filter_and_sorting(client, app):
    with app.app_context():
        db.session.add(Incident(title="Resolved Task", description="d", severity="low", status="resolved"))
        db.session.add(Incident(title="Open Task", description="d", severity="critical", status="open"))
        db.session.commit()

    resp = client.get("/incidents?status=resolved&sort=severity_desc")
    assert resp.status_code == 200
    assert b"Resolved Task" in resp.data
    assert b"Open Task" not in resp.data


def test_incident_to_dict(app):
    with app.app_context():
        incident = Incident(title="Dict Test", description="desc", severity="medium", status="open")
        db.session.add(incident)
        db.session.commit()
        d = incident.to_dict()
        assert d["title"] == "Dict Test"
        assert d["severity"] == "medium"
        assert d["created_at"] is not None

