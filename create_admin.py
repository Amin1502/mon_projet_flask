from app.flask_exercice import app, db, User
from werkzeug.security import generate_password_hash

def create_or_update_admin():
    email = "aminsex@gmail.com"      # tu peux le changer
    password = "admin123"         # tu peux le changer

    # Vérifie si un admin existe déjà avec ce mail
    admin = User.query.filter_by(email=email).first()

    if admin:
        admin.password_hash = generate_password_hash(password)
        admin.role = "admin"
        admin.is_admin = True
        print(f"🔁 Admin mis à jour : {email}")
    else:
        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
            is_admin=True
        )
        db.session.add(admin)
        print(f"✅ Nouvel admin créé : {email}")

    db.session.commit()
    print(f"➡️ Mot de passe : {password}")

if __name__ == "__main__":
    with app.app_context():
        create_or_update_admin()
