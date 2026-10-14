from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    for u in User.query.all():
        u.mot_de_passe = generate_password_hash(u.email)
    db.session.commit()
    print("Terminé :", User.query.count(), "comptes")