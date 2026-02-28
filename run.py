import os
from app.flask_exercice import app, db

if __name__ == "__main__":
    # ✅ DEV seulement : création automatique de la DB (SQLite en local)
    with app.app_context():
        db.create_all()

    # ✅ DEV seulement : debug contrôlé par variable d'environnement
    debug = os.environ.get("FLASK_DEBUG") == "1"

    app.run(port=5001, debug=debug)