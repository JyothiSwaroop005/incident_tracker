"""Flask-WTF forms for incident creation and editing."""
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from config import Config


def _validate_choice(valid_choices: list[str]):
    """Return a WTForms validator that rejects values outside `valid_choices`.

    SelectField already restricts input via `choices`, but we validate
    explicitly too so the same rule is enforced if this form is ever
    driven from raw JSON/API input rather than the rendered <select>.
    """

    def _validator(_form, field):
        if field.data not in valid_choices:
            raise ValidationError(f"Must be one of: {', '.join(valid_choices)}")

    return _validator


class IncidentForm(FlaskForm):
    """Form used for both creating and editing an incident."""

    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(min=3, max=200, message="Title must be between 3 and 200 characters."),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(message="Description is required."),
            Length(max=4000, message="Description is too long."),
        ],
    )
    severity = SelectField(
        "Severity",
        choices=[(s, s.capitalize()) for s in Config.SEVERITIES],
        validators=[DataRequired(), _validate_choice(Config.SEVERITIES)],
    )
    status = SelectField(
        "Status",
        choices=[(s, s.replace("_", " ").capitalize()) for s in Config.STATUSES],
        validators=[DataRequired(), _validate_choice(Config.STATUSES)],
    )
    reported_by = StringField(
        "Reported by",
        validators=[Optional(), Length(max=120)],
        default="Anonymous",
    )
    assigned_to = StringField(
        "Assigned to",
        validators=[Optional(), Length(max=120)],
    )


class DeleteForm(FlaskForm):
    """Empty form whose sole purpose is to carry a CSRF token for deletes."""
    pass
