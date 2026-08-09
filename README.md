# Incident Tracker — Flask Edition

A modern, self-hosted incident management dashboard. Rebuilt from an original
AWS serverless (Lambda + API Gateway + DynamoDB) version into a full Flask
application with a persistent database, server-rendered UI, and a
commercial-SaaS-grade dashboard experience.

## Overview

Incident Tracker lets a team log, triage, and resolve incidents from a single
dashboard: create incidents with severity/status, search and filter the full
list, sort by recency or severity, page through large result sets, and track
who reported and who's assigned. It ships with realistic seed data so the
dashboard is populated the moment you run it.

## Features

- **Dashboard homepage** — animated stat counters (total / open / critical / resolved),
  a severity breakdown doughnut chart (Chart.js), and a recent-incidents feed.
- **Full incident list** — search by title/description, filter by status and
  severity, sort by newest/oldest/severity, server-side pagination.
- **Incident detail view** — full metadata (reporter, assignee, timestamps),
  quick-resolve action, edit and delete from the same screen.
- **Create / edit forms** — Flask-WTF forms with inline validation errors,
  CSRF protection on every state-changing request.
- **Flash notifications** — toast-style, auto-dismissing, color-coded by type.
- **Confirmation dialogs** — modal confirmation before any delete.
- **Empty states** — friendly illustrated messaging when a filter returns nothing
  or no incidents exist yet.
- **Responsive layout** — collapsible sidebar on mobile, fluid grid on tablet/desktop.
- **Row actions dropdown, hover states, sticky topbar, keyboard-accessible forms.**

## Screenshots

_Add screenshots here after running the app locally:_
- `docs/screenshot-dashboard.png` — dashboard homepage
- `docs/screenshot-incidents.png` — incident list with filters
- `docs/screenshot-detail.png` — incident detail view
- `docs/screenshot-create.png` — create incident form

## Technologies Used

| Layer      | Technology |
|------------|------------|
| Backend    | Python 3.12, Flask 3 |
| ORM        | Flask-SQLAlchemy |
| Forms      | Flask-WTF, WTForms (CSRF protection + validation) |
| Database   | SQLite (default, zero setup) |
| Frontend   | Jinja2, Bootstrap 5, vanilla JavaScript |
| Charts     | Chart.js |
| Icons      | Bootstrap Icons |
| Fonts      | Inter, JetBrains Mono |

## Installation

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd incident-tracker-flask
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

The app creates `database.db` automatically on first run and seeds it with
five demo incidents. Visit **http://127.0.0.1:5000** — it redirects to the
dashboard.

To reset to a clean seeded state, stop the app and delete `database.db`,
then run `python app.py` again.

## Environment variables (optional)

| Variable       | Default                          | Purpose |
|----------------|-----------------------------------|---------|
| `SECRET_KEY`   | `dev-secret-key-change-in-production` | Flask session/CSRF signing key. **Set a real secret in production.** |
| `DATABASE_URL` | `sqlite:///database.db`          | SQLAlchemy connection string — point this at Postgres/MySQL for production. |

## Folder structure

```
incident-tracker-flask/
├── app.py                     # application factory + entrypoint + demo seeding
├── config.py                  # configuration (env-driven)
├── models.py                  # SQLAlchemy Incident model
├── forms.py                   # Flask-WTF forms with validation
├── routes.py                  # all view functions (blueprint)
├── requirements.txt
├── database.db                # created automatically on first run
│
├── static/
│   ├── css/style.css          # full design system + component styles
│   ├── js/app.js              # counters, sidebar toggle, toasts, tooltips
│   ├── images/
│   ├── icons/
│   └── animations/
│
├── templates/
│   ├── base.html              # sidebar + topbar shell, flash toasts
│   ├── dashboard.html         # stat cards + chart + recent incidents
│   ├── incidents.html         # searchable/filterable/sortable/paginated table
│   ├── create.html
│   ├── edit.html
│   ├── details.html
│   ├── 404.html
│   └── components/
│       ├── badges.html        # severity/status badge macros
│       ├── empty_state.html   # empty-state illustration macro
│       └── confirm_modal.html # delete-confirmation modal macro
│
└── tests/
    └── test_app.py            # route + validation + CRUD test suite (pytest)
```

## Routes

| Method | Path                             | Purpose |
|--------|-----------------------------------|---------|
| GET    | `/`                               | Redirects to `/dashboard` |
| GET    | `/dashboard`                      | Stats, chart, recent incidents |
| GET    | `/incidents`                      | Full list — search/filter/sort/paginate via query params |
| GET    | `/incident/<id>`                  | Incident detail |
| GET/POST | `/create`                       | Create form / submit |
| GET/POST | `/edit/<id>`                    | Edit form / submit |
| POST   | `/delete/<id>`                    | Delete (CSRF-protected) |
| POST   | `/incident/<id>/quick-resolve`    | Mark resolved without opening the edit form |

Query params on `/incidents`: `q` (search), `status`, `severity`, `sort`
(`created_desc` / `created_asc` / `severity_desc` / `severity_asc`), `page`.

## Testing

```bash
pytest tests/ -v
```

12 tests cover: page loads, create success/validation failures (empty title,
invalid severity), edit, delete, quick-resolve, search filtering, and severity
filtering — run against an in-memory SQLite database, no state left behind.

## Security notes

- CSRF protection on every POST via Flask-WTF (`CSRFProtect`).
- All database access goes through the SQLAlchemy ORM — no raw SQL, no
  injection surface.
- Jinja2 auto-escapes all template output by default.
- Server-side validation on every form field (title/description required,
  severity/status restricted to a fixed enum) — never trusts client-side
  `<select>` restrictions alone.
- `SECRET_KEY` and `DATABASE_URL` are environment-driven; the checked-in
  defaults are for local development only and must be overridden in any
  real deployment.

## What's intentionally out of scope

- No authentication/authorization — anyone with network access can create,
  edit, or delete incidents. Would add Flask-Login + role-based access next.
- No production WSGI server config (this runs Flask's dev server) — for
  production, put this behind Gunicorn/uWSGI + Nginx.
- SQLite is fine for a demo/single-instance deployment; swap `DATABASE_URL`
  to Postgres for anything with concurrent writers.
