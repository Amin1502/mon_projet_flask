# forms_exercice.py
from wtforms import IntegerField
from wtforms.validators import NumberRange,EqualTo

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, Email, Length, Regexp

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Mot de passe",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$',
                   message="1 majuscule, 1 chiffre, 1 caractère spécial")
        ]
    )
    submit = SubmitField("S'inscrire")



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    
    submit = SubmitField("Se connecter")

class ProfileForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("Mettre à jour")



class UtilisateurForm(FlaskForm):
    nom = StringField("Nom", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    age = IntegerField("Âge", validators=[DataRequired(), NumberRange(min=18)])
    submit = SubmitField("Enregistrer")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Ancien mot de passe", validators=[DataRequired()])
    new_password = PasswordField(
        "Nouveau mot de passe",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$',
                message="1 majuscule, 1 chiffre, 1 caractère spécial"
            )
        ]
    )
    confirm_password = PasswordField(
        "Confirmer le nouveau mot de passe",
        validators=[
            DataRequired(),
            EqualTo('new_password', message="Les mots de passe ne correspondent pas.")
        ]
    )
    submit = SubmitField("Changer le mot de passe")


class MessageForm(FlaskForm):
    subject = StringField(
        "Sujet",
        validators=[DataRequired(), Length(max=150)]
    )
    content = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField("Envoyer")
