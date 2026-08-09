"""HTTP routes for the incident tracker dashboard."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from config import Config
from forms import DeleteForm, IncidentForm
from models import Incident, db

bp = Blueprint("incidents", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(query, args):
    """Apply search/status/severity filters from query args to a query."""
    search = args.get("q", "").strip()
    status = args.get("status", "").strip()
    severity = args.get("severity", "").strip()

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Incident.title.ilike(like), Incident.description.ilike(like))
        )
    if status in Config.STATUSES:
        query = query.filter(Incident.status == status)
    if severity in Config.SEVERITIES:
        query = query.filter(Incident.severity == severity)
    return query


def _apply_sort(query, args):
    """Apply sort order from query args to a query."""
    sort = args.get("sort", "created_desc")

    if sort == "created_asc":
        return query.order_by(Incident.created_at.asc())
    if sort == "severity_desc":
        # SQLite has no native enum ordering, so sort in Python after fetch
        # for severity; for simplicity here we approximate via CASE ordering.
        return query.order_by(
            db.case(
                {sev: weight for sev, weight in Incident.SEVERITY_WEIGHT.items()},
                value=Incident.severity,
            ).desc()
        )
    if sort == "severity_asc":
        return query.order_by(
            db.case(
                {sev: weight for sev, weight in Incident.SEVERITY_WEIGHT.items()},
                value=Incident.severity,
            ).asc()
        )
    # default: created_desc
    return query.order_by(Incident.created_at.desc())


def _stats() -> dict:
    """Compute summary statistics shown on the dashboard widgets."""
    total = Incident.query.count()
    open_count = Incident.query.filter(Incident.status == "open").count()
    investigating_count = Incident.query.filter(Incident.status == "investigating").count()
    critical_open = Incident.query.filter(
        Incident.severity == "critical", Incident.status != "resolved"
    ).count()
    high_open = Incident.query.filter(
        Incident.severity == "high", Incident.status != "resolved"
    ).count()
    medium_open = Incident.query.filter(
        Incident.severity == "medium", Incident.status != "resolved"
    ).count()
    low_open = Incident.query.filter(
        Incident.severity == "low", Incident.status != "resolved"
    ).count()
    resolved = Incident.query.filter(Incident.status == "resolved").count()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    resolved_today = Incident.query.filter(
        Incident.status == "resolved", Incident.updated_at >= today_start
    ).count()

    return {
        "total": total,
        "open": open_count,
        "investigating": investigating_count,
        "pending": open_count + investigating_count,
        "critical": critical_open,
        "high": high_open,
        "medium": medium_open,
        "low": low_open,
        "resolved": resolved,
        "resolved_today": resolved_today,
    }


def _severity_breakdown() -> dict:
    """Counts per severity, used to feed the Chart.js doughnut chart."""
    counts = {sev: 0 for sev in Config.SEVERITIES}
    for severity, count in (
        db.session.query(Incident.severity, db.func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    ):
        counts[severity] = count
    return counts


def _status_breakdown() -> dict:
    """Counts per status, used to feed the status distribution chart."""
    counts = {status: 0 for status in Config.STATUSES}
    for status, count in (
        db.session.query(Incident.status, db.func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    ):
        counts[status] = count
    return counts


def _weekly_activity() -> dict:
    """Incidents reported per day for the last 7 days (oldest first)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    labels = [] 
    counts = []
    for i in range(6, -1, -1):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = Incident.query.filter(
            Incident.created_at >= day_start, Incident.created_at < day_end
        ).count()
        labels.append(day_start.strftime("%a"))
        counts.append(count)
    return {"labels": labels, "counts": counts}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    """Landing route — redirects to the dashboard."""
    return redirect(url_for("incidents.dashboard"))


@bp.route("/dashboard")
def dashboard():
    """Dashboard homepage: stats, charts, and recent incidents."""
    stats = _stats()
    breakdown = _severity_breakdown()
    status_breakdown = _status_breakdown()
    weekly = _weekly_activity()
    recent = Incident.query.order_by(Incident.created_at.desc()).limit(6).all()
    delete_form = DeleteForm()
    return render_template(
        "dashboard.html",
        stats=stats,
        breakdown=breakdown,
        status_breakdown=status_breakdown,
        weekly=weekly,
        recent=recent,
        delete_form=delete_form,
    )


@bp.route("/incidents")
def incident_list():
    """Full incident list with search, filters, sort, and pagination."""
    query = Incident.query
    query = _apply_filters(query, request.args)
    query = _apply_sort(query, request.args)

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=Config.INCIDENTS_PER_PAGE, error_out=False)

    delete_form = DeleteForm()
    # Args without 'page' so pagination links can safely add their own page=N
    filter_args = {k: v for k, v in request.args.items() if k != "page"}
    return render_template(
        "incidents.html",
        pagination=pagination,
        incidents=pagination.items,
        severities=Config.SEVERITIES,
        statuses=Config.STATUSES,
        delete_form=delete_form,
        args=request.args,
        filter_args=filter_args,
    )


@bp.route("/incident/<int:incident_id>")
def incident_detail(incident_id: int):
    """Single incident detail view."""
    incident = db.get_or_404(Incident, incident_id)
    delete_form = DeleteForm()
    return render_template("details.html", incident=incident, delete_form=delete_form)


@bp.route("/create", methods=["GET", "POST"])
def create_incident():
    """Create a new incident."""
    form = IncidentForm()
    if form.validate_on_submit():
        incident = Incident(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            severity=form.severity.data,
            status=form.status.data,
            reported_by=(form.reported_by.data or "Anonymous").strip(),
            assigned_to=(form.assigned_to.data or "").strip() or None,
        )
        db.session.add(incident)
        db.session.commit()
        flash(f'Incident "{incident.title}" created.', "success")
        return redirect(url_for("incidents.incident_detail", incident_id=incident.id))

    return render_template("create.html", form=form)


@bp.route("/edit/<int:incident_id>", methods=["GET", "POST"])
def edit_incident(incident_id: int):
    """Edit an existing incident."""
    incident = db.get_or_404(Incident, incident_id)
    form = IncidentForm(obj=incident)

    if form.validate_on_submit():
        incident.title = form.title.data.strip()
        incident.description = form.description.data.strip()
        incident.severity = form.severity.data
        incident.status = form.status.data
        incident.reported_by = (form.reported_by.data or "Anonymous").strip()
        incident.assigned_to = (form.assigned_to.data or "").strip() or None
        db.session.commit()
        flash(f'Incident "{incident.title}" updated.', "success")
        return redirect(url_for("incidents.incident_detail", incident_id=incident.id))

    return render_template("edit.html", form=form, incident=incident)


@bp.route("/delete/<int:incident_id>", methods=["POST"])
def delete_incident(incident_id: int):
    """Delete an incident. CSRF-protected via DeleteForm."""
    form = DeleteForm()
    if not form.validate_on_submit():
        abort(400)

    incident = db.get_or_404(Incident, incident_id)
    title = incident.title
    db.session.delete(incident)
    db.session.commit()
    flash(f'Incident "{title}" deleted.', "info")
    return redirect(url_for("incidents.incident_list"))


@bp.route("/incident/<int:incident_id>/quick-resolve", methods=["POST"])
def quick_resolve(incident_id: int):
    """Convenience action: mark an incident resolved from a list/table row."""
    form = DeleteForm()
    if not form.validate_on_submit():
        abort(400)

    incident = db.get_or_404(Incident, incident_id)
    incident.status = "resolved"
    db.session.commit()
    flash(f'Incident "{incident.title}" marked resolved.', "success")
    return redirect(request.referrer or url_for("incidents.incident_list"))
