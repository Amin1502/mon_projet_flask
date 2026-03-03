from flask_migrate import Migrate

from flask_wtf import CSRFProtect
from app.forms_exercice import RegisterForm, LoginForm, UtilisateurForm, ProfileForm, ChangePasswordForm,MessageForm
import os
from datetime import datetime



from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from flask import Flask, render_template, request, redirect, flash, Response, abort
from flask_sqlalchemy import SQLAlchemy
import re
import io
import csv
from functools import wraps
from flask import redirect, url_for, flash


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for("login"))
        if not current_user.is_admin:
            flash("Accès réservé à l’administrateur.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY non définie dans les variables d'environnement")


csrf = CSRFProtect(app)

login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = 'login'  # si l'utilisateur non connecté essaie d’accéder à une page protégée → redirection vers /login

db_url = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///flask_exercice.db"
db = SQLAlchemy(app)




# Nouveau modèle User


class User(db.Model, UserMixin):  # 👈 ajout de UserMixin
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # rôle par défaut : user
    is_admin = db.Column(db.Boolean, default=False)  # 👈 nouveau champ
    # méthode pour définir un mot de passe (hashé)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # méthode pour vérifier le mot de passe entré
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    messages = db.relationship('Message', backref='author', lazy=True)


class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
   

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Qui a envoyé le message (user connecté)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Contenu du message
    subject = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Suivi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Utilisateur {self.nom}>'


migrate = Migrate(app, db)


@app.route('/hello')
def accueil():
    return "hello"

@app.route('/bravo/')
def bravo():
    return "Bravo, tu codes avec Flask !"

@app.route('/utilisateurs')
def afficher_utilisateurs():
    utilisateurs = Utilisateur.query.all()
    return render_template('liste_utilisateurs.html', utilisateurs=utilisateurs)


@app.route('/presentation')
def presentation():
    return """
    <h1>Bienvenue sur ma page</h1>
    <p>Je m'appelle Amin Goudi et j'apprends Flask.</p>
    <p>Voici mes animaux préférés :</p>
    Chien<br>Chat<br>Oiseau
    """
@app.route('/presentation/<prenom>')
def presentation_prenom(prenom):
    return render_template('presentation.html', prenom=prenom)

@app.route('/hello/<prenom>')
def hello(prenom):
    return f"Salut, {prenom} !"

@app.route('/double/<int:x>')
def double(x):
    y = 2 * x
    return f"Le double de {x} est {y} !"

@app.route('/quadruple/<int:x>')
def quadruple(x):
    y = 4 * x
    return f"Le quadruple de {x} est {y} !"

@app.route('/animaux/')
def animaux():
    return """
    Chien<br>
    Chat<br>
    Oiseau
    """
@app.route('/carre/<int:n>')
def carre(n):
    y = n * n
    return f"Le carré de {n} est {y} !"

@app.route('/formulaire', methods=['GET', 'POST'])
def formulaire():
    form = UtilisateurForm()

    if form.validate_on_submit():   # WTForms valide tout (CSRF, email, âge…)
        nom = form.nom.data
        email = form.email.data
        age = form.age.data

        # Vérification email déjà utilisé
        utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
        if utilisateur_existant:
            flash("Cet email est déjà utilisé.", "danger")
            return render_template("form_exercice.html", form=form)

        nouvel_utilisateur = Utilisateur(nom=nom, email=email, age=age)
        db.session.add(nouvel_utilisateur)
        db.session.commit()

        flash("Utilisateur ajouté avec succès !", "success")
        return redirect('/utilisateurs')

    return render_template("form_exercice.html", form=form)


@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
@admin_required
@login_required

def modifier_utilisateur(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    if request.method == 'POST':
        utilisateur.nom = request.form['nom']
        utilisateur.email = request.form['email']
        utilisateur.age = request.form['age']

        db.session.commit()
        return redirect('/utilisateurs')  # Redirection vers la liste

    return render_template('modif_exos_utilisateur.html', utilisateur=utilisateur)

@app.route('/supprimer/<int:id>', methods=['POST'])
@login_required
@admin_required 

def supprimer_utilisateur(id):
    utilisateur = Utilisateur.query.get_or_404(id)
    db.session.delete(utilisateur)
    db.session.commit()
    flash(f"Utilisateur supprimé.", "success")

    return redirect('/utilisateurs')


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    query = request.args.get('q')

    # SECTION 1 — Comptes User (auth, admin)
    if query:
        users = User.query.filter(
            (User.email.contains(query)) |
            (User.role.contains(query))
        ).all()
    else:
        users = User.query.all()

    # SECTION 2 — Fiches Utilisateur (formulaire)
    if query:
        utilisateurs = Utilisateur.query.filter(
            (Utilisateur.nom.contains(query)) |
            (Utilisateur.email.contains(query)) |
            (Utilisateur.age == int(query) if query.isdigit() else False)
        ).all()
    else:
        utilisateurs = Utilisateur.query.all()

    # 🔹 STATS ADMIN
    total_users = User.query.count()                  # nombre total de comptes User
    admin_count = User.query.filter_by(is_admin=True).count()  # nombre d’admins
    form_users_count = Utilisateur.query.count()      # nombre de fiches "Utilisateurs"

    return render_template(
        "dashboard.html",
        users=users,
        utilisateurs=utilisateurs,
        query=query,
        total_users=total_users,
        admin_count=admin_count,
        form_users_count=form_users_count
    )


@app.route('/login_history')
@login_required
@admin_required
def login_history():
    logs = (
        db.session.query(LoginLog, User)
        .join(User, LoginLog.user_id == User.id)
        .order_by(LoginLog.timestamp.desc())
        .all()
    )
    return render_template("login_history.html", logs=logs)


@app.route('/export_form_users')
@login_required
@admin_required

def export_form_users():
    utilisateurs = Utilisateur.query.all()

    # Création d’un tampon mémoire (simule un fichier)
    output = io.StringIO()
    writer = csv.writer(output)

    # En-têtes
    writer.writerow(["ID", "Nom", "Email", "Âge"])

    # Données
    for u in utilisateurs:
        writer.writerow([u.id, u.nom, u.email, u.age])

    # Récupérer le contenu CSV
    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=utilisateurs.csv"}
    )



@app.route('/export_users')
@login_required
@admin_required
def export_users():
    users = User.query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # En-têtes
    writer.writerow([
        "ID",
        "Email",
        "Role",
        "Is Admin"
    ])

    # Données
    for user in users:
        writer.writerow([
            user.id,
            user.email,
            user.role,
            user.is_admin
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users_auth.csv"
        }
    )







@app.route('/')
def home():
    return render_template('home_exos.html')

@app.route("/test_base")
def test_base():
    return render_template("test_base_exos.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():  # déclenché sur POST si le formulaire est valide
        email = form.email.data
        password = form.password.data

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Cet email est déjà utilisé.", "danger")
            return redirect('/register')

        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
        return redirect('/login')  # rediriger vers la page de login après inscription

    # GET initial ou erreurs de validation -> on ré-affiche le form
    return render_template('exos_register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():  # Si POST et que les champs sont valides
        email = form.email.data
        password = form.password.data

        # Recherche de l'utilisateur dans la base
        user = User.query.filter_by(email=email).first()

        # Vérification du mot de passe
        if user and user.check_password(password):
            login_user(user)
            # 🔎 Enregistrer le log
            
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'N/A')
            log = LoginLog(user_id=user.id, ip=ip, user_agent=user_agent)
            db.session.add(log)
            db.session.commit()
            
            
            flash("Connexion réussie !", "success")
            return redirect("/dashboard")  # Redirection après login
        else:
            flash("Email ou mot de passe invalide.", "danger")

    # GET initial ou erreurs de validation → on réaffiche le formulaire
    return render_template("exos_login.html", form=form)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect('/login')

@app.route('/admin')
@admin_required
def admin_dashboard():
    return "<h1>👑 Espace administrateur réservé !</h1><p>Bienvenue, admin.</p>"



@app.route('/make_admin/<int:id>')
@login_required
@admin_required
def make_admin(id):
    user = User.query.get_or_404(id)

    # toggle admin
    user.is_admin = not user.is_admin

    # rôle lié
    user.role = "admin" if user.is_admin else "user"

    db.session.commit()

    flash("Rôle mis à jour avec succès.", "success")
    return redirect('/dashboard')


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    form = ProfileForm(obj=user)  # pré-remplit avec l'email du user ciblé

    if form.validate_on_submit():
        # Vérifier que l'email n'est pas déjà pris par un autre compte
        existing = User.query.filter(
            User.email == form.email.data,
            User.id != user.id
        ).first()

        if existing:
            flash("Cet email est déjà utilisé par un autre compte.", "danger")
            return render_template("edit_user.html", form=form, user=user)

        # Mise à jour de l'email
        user.email = form.email.data
        db.session.commit()

        flash("Compte utilisateur mis à jour avec succès.", "success")
        return redirect(url_for('dashboard'))

    return render_template("edit_user.html", form=form, user=user)




@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    form = ProfileForm(obj=current_user)  # pré-remplit avec l'email actuel

    if form.validate_on_submit():
        new_email = form.email.data

        # Vérifier que l'email n'est pas déjà pris par quelqu'un d'autre
        existing = User.query.filter(
            User.email == new_email,
            User.id != current_user.id
        ).first()

        if existing:
            flash("Cet email est déjà utilisé.", "danger")
            return render_template("profil_exos.html", form=form)

        # Mise à jour de l'email
        current_user.email = new_email
        db.session.commit()
        flash("Profil mis à jour.", "success")
        return redirect('/dashboard')

    return render_template("profil_exos.html", form=form)



@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Vérifier l'ancien mot de passe
        if not current_user.check_password(form.old_password.data):
            flash("Ancien mot de passe incorrect.", "danger")
            return render_template("change_password.html", form=form)

        # Mettre à jour le mot de passe
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash("Mot de passe mis à jour avec succès.", "success")
        return redirect(url_for('profil'))

    return render_template("change_password.html", form=form)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Sécurité : on empêche de supprimer son propre compte
    if user.id == current_user.id:
        flash("Tu ne peux pas supprimer ton propre compte admin.", "warning")
        return redirect(url_for('dashboard'))

    db.session.delete(user)
    db.session.commit()

    flash("Compte utilisateur supprimé avec succès.", "success")
    return redirect(url_for('dashboard'))


@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    form = MessageForm()

    if form.validate_on_submit():
        # 1) Récupérer les données du formulaire
        subject = form.subject.data
        content = form.content.data

        # 2) Créer un nouvel objet Message lié à l'utilisateur connecté
        message = Message(
            user_id=current_user.id,
            subject=subject,
            content=content
        )

        # 3) Enregistrer en base
        db.session.add(message)
        db.session.commit()

        # 4) Feedback + redirection
        flash("Message envoyé avec succès.", "success")
        return redirect(url_for('contact'))

    # GET initial ou formulaire invalide → on réaffiche la page
    return render_template("contact.html", form=form)



@app.route('/admin/messages', methods=['GET'])
@login_required
@admin_required
def admin_messages():
    messages = (
        db.session.query(Message, User)
        .join(User, Message.user_id == User.id)
        .order_by(Message.created_at.desc())
        .all()
    )
    return render_template("admin_messages.html", messages=messages)


@app.route('/admin/messages/<int:message_id>/read', methods=['POST'])
@login_required
@admin_required
def mark_message_read(message_id):
    message = Message.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash("Message marqué comme lu.", "success")
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/<int:message_id>', methods=['GET'])
@login_required
@admin_required
def admin_message_detail(message_id):
    message = Message.query.get_or_404(message_id)
    user = User.query.get(message.user_id)
    return render_template("admin_message_detail.html", message=message, user=user)



@app.route('/export_logs')
@login_required
@admin_required
def export_logs():
    logs = (
        db.session.query(LoginLog, User)
        .join(User, LoginLog.user_id == User.id)
        .order_by(LoginLog.timestamp.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # En-têtes CSV
    writer.writerow([
        "Email utilisateur",
        "Date connexion",
        "Adresse IP",
        "Navigateur"
    ])

    # Données
    for log, user in logs:
        writer.writerow([
            user.email,
            log.timestamp,
            log.ip,
            log.user_agent
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs_connexions.csv"}
    )




@app.route('/import_csv', methods=['POST'])
@login_required
@admin_required
def import_csv():
    file = request.files.get('file')

    if not file or file.filename == '':
        flash("Aucun fichier sélectionné.", "danger")
        return redirect(url_for('dashboard'))

    if not file.filename.endswith('.csv'):
        flash("Le fichier doit être au format CSV.", "danger")
        return redirect(url_for('dashboard'))

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)

    added = 0
    skipped_invalid = 0
    skipped_duplicate = 0

    for row in reader:
        nom = row.get('Nom')
        email = row.get('Email')
        age = row.get('Age')

        email = (email or "").strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            skipped_invalid += 1
            continue

        if not nom or not email or not age:
            skipped_invalid += 1
            continue

        utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
        if utilisateur_existant:
            skipped_duplicate += 1
            continue

        nouvel_utilisateur = Utilisateur(
            nom=nom,
            email=email,
            age=int(age)
        )

        db.session.add(nouvel_utilisateur)
        added += 1

    db.session.commit()

    flash(
        f"Import terminé — Ajoutés: {added} | Doublons ignorés: {skipped_duplicate} | Lignes invalides ignorées: {skipped_invalid}",
        "success"
    )
    return redirect(url_for('dashboard'))





@app.route('/import_csv', methods=['GET'])
@login_required
@admin_required
def import_csv_form():
    return render_template('import_csv.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500




