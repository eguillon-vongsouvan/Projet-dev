from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    PasswordField,
    StringField,
    SelectField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from wtforms.fields import TimeField


def _validate_time_str(form, field):
    # Contrôle minimal "HH:MM"
    value = field.data.strftime("%H:%M") if hasattr(field.data, "strftime") else str(field.data)
    if len(value) != 5 or value[2] != ":":
        raise ValidationError("Format de l'heure invalide (attendu HH:MM).")


class LoginForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=50)],
    )
    password = PasswordField(
        "Mot de passe",
        validators=[DataRequired(), Length(min=6, max=128)],
    )


class CreateUserForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6, max=128)])
    role = SelectField(
        "Rôle",
        choices=[("ADMIN", "Administrateur"), ("PROFESSOR", "Professeur"), ("STUDENT", "Étudiant")],
        validators=[DataRequired()],
    )


class CreateClassForm(FlaskForm):
    name = StringField("Nom de la classe", validators=[DataRequired(), Length(min=3, max=100)])
    teacher_username = StringField(
        "Nom du professeur (username)",
        validators=[Optional(), Length(min=1, max=50)],
    )


class AssignStudentForm(FlaskForm):
    student_username = StringField("Nom de l'étudiant (username)", validators=[DataRequired(), Length(min=3, max=50)])


class CreateScheduleForm(FlaskForm):
    day_of_week = IntegerField("Jour (1=Lun ... 7=Dim)", validators=[DataRequired(), NumberRange(min=1, max=7)])
    start_time = TimeField("Heure début", validators=[DataRequired()], format="%H:%M")
    end_time = TimeField("Heure fin", validators=[DataRequired()], format="%H:%M")
    location = StringField("Lieu", validators=[Optional(), Length(max=100)])


class CreateAssessmentForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(min=3, max=100)])
    due_date = DateField("Date limite (optionnel)", validators=[Optional()])


class CreateHomeworkForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired(), Length(min=3, max=140)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    due_date = DateField("Date limite (optionnel)", validators=[Optional()])


class RecordAbsenceForm(FlaskForm):
    student_username = StringField("Étudiant (username)", validators=[DataRequired(), Length(min=3, max=50)])
    absence_date = DateField("Date", validators=[DataRequired()])
    reason = StringField("Motif (optionnel)", validators=[Optional(), Length(max=255)])


class CsrfForm(FlaskForm):
    """
    Utilisé quand on a un formulaire HTML dynamique (champs générés côté Jinja)
    mais qu'on veut quand même bénéficier du token CSRF Flask-WTF.
    """

    pass

