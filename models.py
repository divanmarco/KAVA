from datetime import date
from decimal import Decimal
from flask.config import T
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_login import UserMixin
from extensions import db, login
import enum
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash


class RoleEnum(enum.Enum):
    GERANT = "Gérant"
    CAISSIER = "Caissier"
    SERVEUR = "Serveur"
    LIVREUR = "Livreur"
    DAF = "DAF"


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    quartier = db.Column(db.String(100), nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(RoleEnum),
        nullable=False,
    )
    status = db.Column(
        db.Enum("Actif", "Inactif", "Bloqué", name="status_enum"),
        nullable=False,
    )

    @staticmethod
    def generer_mot_de_passe(longueur=10):
        caracteres = string.ascii_letters + string.digits
        return ''.join(secrets.choice(caracteres) for _ in range(longueur))



    def set_password(self, email):
        self.password_hash = generate_password_hash(email)

    def check_password(self, email):
        return check_password_hash(self.password_hash, email)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
   

class Client(db.Model):
    __tablename__ = "client"

    id_client = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    numero_de_telephone = db.Column(db.String(50), nullable=False)
    quartier_de_residence = db.Column(db.String(50), nullable=False)



class Produits(db.Model):
    __tablename__ = "produits"

    id_produit = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    prix_achat = db.Column(db.Numeric(10, 2), nullable=False)
    prix_de_vente = db.Column(db.Numeric(10, 2), nullable=False)
    quantite_en_stock = db.Column(db.Integer, nullable=False)
    categorie = db.Column(db.String(50), nullable=True)
    status = db.Column(
        db.Enum("En stock", "Épuisé", name="status_produit_enum"),
        nullable=False,)

    @staticmethod
    def generer_code_produit(longueur=8):
        caracteres = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(caracteres) for _ in range(longueur))


class Commande(db.Model):
    __tablename__ = "commande"

    id_commande = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, db.ForeignKey("client.id_client"), nullable=False)
    name = db.Column(db.String(50), nullable=False)



class Ligne_Commande(db.Model):
    __tablename__ = "ligne_commande"

    id_ligne_de_commande = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey("commande.id_commande"), nullable=False)
    id_produit = db.Column(db.Integer, db.ForeignKey("produits.id_produit"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    quantite = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default="0")


class Vente(db.Model):
    __tablename__ = "vente"

    id_vente = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey("commande.id_commande"), nullable=False)
    montant_percue = db.Column(db.Numeric(10, 2), nullable=False)
    montant_attendu = db.Column(db.Numeric(10, 2), nullable=False)
    statut = db.Column(
        db.Enum("payee", "partielle", "impayee", name="statut_vente_enum"),
        nullable=False,
        default="impayee"
    )
    mode_vente = db.Column(
        db.Enum("comptant", "credit", "livraison", name="mode_vente_enum"),
        nullable=False
    )
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_vente = db.Column(db.DateTime, nullable=False)


class Livraison(db.Model):
    __tablename__ = "livraison"

    id = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey("commande.id_commande"), nullable=False)
    id_client = db.Column(db.Integer, db.ForeignKey("client.id_client"), nullable=False)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    adresse_livraison = db.Column(db.String(200), nullable=False)
    date_livraison_prevue = db.Column(db.DateTime, nullable=False)
    date_livraison_effective = db.Column(db.DateTime, nullable=True)
    statut = db.Column(
        db.Enum("en_cours", "livree", "annulee", name="statut_livraison_enum"),
        nullable=False,
        default="en_cours"
    )


class Rapport_de_Compte(db.Model):
    __tablename__ = "rapport_de_compte"

    id_rapport = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)

    date_debut = db.Column(db.DateTime, nullable=True)
    date_fin =db.Column(db.DateTime, nullable=True)
    type = db.Column(db.String(50), nullable=True) 

    statut = db.Column(
        db.Enum("brouillon", "publie", name="statut_rapport_enum"),
        nullable=False,
        default="brouillon"
    )


class Commentaire(db.Model):
    __tablename__ = "commentaire"

    id_commentaire = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_generation = db.Column(db.DateTime, nullable=False)


class Bilan(db.Model):
    __tablename__ = "bilan"

    id_bilan = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    montant_total = db.Column(db.Numeric(10, 2), nullable=False)
    date_generation = db.Column(db.DateTime, nullable=False)


class Session(db.Model):
    __tablename__ = "session"

    id_session = db.Column(db.String(50), primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    statut_session = db.Column(
        db.Enum("active", "expiree", "deconnectee", name="statut_session_enum"),
        nullable=False,
        default="active"
    )
    date_connexion = db.Column(db.DateTime, nullable=False)


# class LoginForm(FlaskForm):
#     username = StringField(
#         validators=[DataRequired(), Length(min=4, max=20)],
#         render_kw={"placeholder": "username", "id": "txt"}
#     )
#     password = PasswordField(
#         validators=[DataRequired(), Length(min=4, max=20)],
#         render_kw={"placeholder": "password", "id": "mdp", "class": "eye-icon"}
#     )
#     submit = SubmitField('Login')

