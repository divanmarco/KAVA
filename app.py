from decimal import Decimal, InvalidOperation
from commande import creer_commande, StockInsuffisant
from flask_login import current_user, login_required
from flask import Flask, render_template, redirect , request, session , url_for, flash
from pymysql import IntegrityError
from config import Config
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt 
from extensions import db, login, migrate, bcrypt
from models import User,Produits
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import secrets
from sqlalchemy import or_
import re
import os
from sqlalchemy import func
from datetime import datetime
from models import Commentaire
from flask_login import login_required, current_user
from models import Rapport_de_Compte


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/kava'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login.init_app(app)
login.login_view = 'login'
db.init_app(app)
migrate.init_app(app,db)
bcrypt.init_app(app)
app.secret_key = "6bf00abdb73b68bad0a2711b1b3c6ff71e162ea5ff7665b3e3830b3b1950feb2"  
app.config.from_object(Config)
from models import * 
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()
from sqlalchemy import desc

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    commandes_recentes = (
        db.session.query(
            Commande.id_commande,
            Client.name.label('client_name'),
            Vente.montant_attendu,
            Vente.montant_percue,
            Vente.statut,
        )
        .join(Client, Commande.id_client == Client.id_client)
        .outerjoin(Vente, Vente.id_commande == Commande.id_commande)
        .order_by(desc(Commande.id_commande))
        .limit(5)
        .all()
    )
    return render_template('html/index.html', commandes_recentes=commandes_recentes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(name=name).first()
        if not user or user.email != password:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
        elif user.role.value  != 'Gérant':
            flash("Seul le Gérant peut se connecter pour l'instant.", "warning")
        else:
            login_user(user)
            flash(f"Bienvenue {user.name} !")
            return redirect(url_for('index'))

    return render_template('html/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None) 
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for('login'))


@app.route("/settings.html", methods=["GET", "POST"])
def settings():
    return render_template("html/settings.html")




@app.route("/forgot-password.html", methods=["GET", "POST"])
def forgot_password():
    return render_template("html/forgot-password.html")




@app.route("/profile.html", methods=["GET", "POST"])
def profile():
    return render_template("html/profile.html")


# Users Management Routes
@app.route("/add-user.html", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        telephone = request.form.get("telephone")
        ville = request.form.get("ville")
        quartier = request.form.get("quartier")
        role = request.form.get("role")
        status = request.form.get("status")

        if not name:
            flash("Le nom est obligatoire.", "danger")
            return render_template("html/users/add-user.html")

        if not email:
            flash("L'email est obligatoire.", "danger")
            return render_template("html/users/add-user.html")

        if not telephone:
            flash("Le numéro de téléphone est obligatoire.", "danger")
            return render_template("html/users/add-user.html")

        if not quartier:
            flash("Le quartier de résidence est obligatoire.", "danger")
            return render_template("html/users/add-user.html")

        mot_de_passe_clair = User.generer_mot_de_passe()
        mot_de_passe_hash = generate_password_hash(mot_de_passe_clair)

        nouvel_utilisateur = User(
            name=name,
            email=email,
            matricule=secrets.token_hex(4),
            telephone=telephone,
            ville=ville,
            quartier=quartier,
            mot_de_passe=mot_de_passe_hash,
            role=RoleEnum(role),
            status=status
        )

        try:
            db.session.add(nouvel_utilisateur)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Cet email est déjà utilisé par un autre utilisateur.", "danger")
            return render_template("html/users/add-user.html")

        flash(f"Utilisateur créé avec succès")
        return redirect(url_for("users"))

    return render_template("html/users/add-user.html")


@app.route("/users/edit-user.html/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == "POST":
        user.name = request.form.get("name")
        user.email = request.form.get("email")
        user.telephone = request.form.get("telephone")
        user.ville = request.form.get("ville")
        user.quartier = request.form.get("quartier")
        user.role = RoleEnum(request.form.get("role"))
        user.status = request.form.get("status")

        db.session.commit()
        return redirect(url_for("users"))
    return render_template("html/users/edit-user.html", user=user)

@app.route("/user-details/<int:id>")
def user_details(id):
    user = User.query.get_or_404(id)
    return render_template("html/users/user-details.html", user=user)

@app.route("/delete-user/<int:id>", methods=["POST"])
def delete_user(id):
    user = User.query.get_or_404(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("users"))

@app.route('/users')
def users():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)

    users_query = User.query
    if query:
        users_query = users_query.filter(
            User.name.ilike(f'%{query}%') |
            User.role.ilike(f'%{query}%') |
            User.ville.ilike(f'%{query}%') |
            User.quartier.ilike(f'%{query}%') |
            User.status.ilike(f'%{query}%') |
            User.email.ilike(f'%{query}%')
        )

    users_page = users_query.paginate(page=page, per_page=5, error_out=False)

    return render_template('html/users/users.html', users=users_page, q=query)




# Products Management Routes
@app.route("/add_product.html", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        prix_achat = request.form.get("prix_achat")
        prix_de_vente = request.form.get("prix_de_vente")
        quantite_en_stock = request.form.get("quantite_en_stock")
        categorie = request.form.get("categorie")
        status = request.form.get("status")

        if not name:
            flash("Le nom est obligatoire.", "danger")
            return render_template("html/product/add-product.html")

        if not prix_achat:
            flash("Le prix d'achat est obligatoire.", "danger")
            return render_template("html/product/add_product.html")

        if not prix_de_vente:
            flash("Le prix de vente est obligatoire.", "danger")
            return render_template("html/product/add_product.html")

        if not quantite_en_stock:
            flash("La quantité en stock est obligatoire.", "danger")
            return render_template("html/product/add_product.html")

        if not categorie:
            flash("La catégorie est obligatoire.", "danger")
            return render_template("html/product/add_product.html")

        if not status:  
            flash("Le statut est obligatoire.", "danger")
            return render_template("html/product/add_product.html")

        if int(quantite_en_stock) <= 0 :
            product.status = "Épuisé"
        else :
            product.status = "En stock"
            

        nouveau_produit = Produits(
            name=name,
            prix_achat=prix_achat,
            prix_de_vente=prix_de_vente,
            quantite_en_stock=quantite_en_stock,
            categorie=categorie,
            status=status
        )

        try:
            db.session.add(nouveau_produit)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Une erreur s'est produite lors de l'ajout du produit.", "danger")
            return render_template("html/product/add_product.html")

        return redirect(url_for('product'))
    return render_template("html/product/add_product.html")


@app.route("/product/edit_product.html/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    product = Produits.query.get_or_404(id)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.prix_achat = request.form.get("prix_achat")
        product.prix_de_vente = request.form.get("prix_de_vente")
        quantite_en_stock = request.form.get("quantite_en_stock")
        product.quantite_en_stock = quantite_en_stock
        product.categorie = request.form.get("categorie")
        product.status = request.form.get("status")

        if int(quantite_en_stock) <= 0 :
            product.status = "Épuisé"
        else :
            product.status = "En stock"

        db.session.commit()
        return redirect(url_for("product"))
    return render_template("html/product/edit_product.html", product=product)


@app.route("/product/product_details/<int:id>")
def product_details(id):
    product = Produits.query.get_or_404(id)
    return render_template("html/product/product_details.html", product=product)

@app.route("/delete-product/<int:id>", methods=["POST"])
def delete_product(id):
    product = Produits.query.get_or_404(id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for("product"))


@app.route('/product')
def product():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)

    product_query = Produits.query
    if query:
        product_query = product_query.filter (
            Produits.name.ilike(f'%{query}%') | 
            Produits.categorie.ilike(f'%{query}%') |
            Produits.status.ilike(f'%{query}%')|
            Produits.prix_achat.ilike(f'%{query}%') |
            Produits.prix_de_vente.ilike(f'%{query}%') 
        )

    product_page = product_query.paginate(page=page, per_page=5, error_out=False)

    return render_template('html/product/product.html', product=product_page, q=query)




# Charts Managements roads 
@app.route("/add_charts.html", methods=["GET", "POST"])
def add_charts():
    if request.method == "POST":
        name = request.form.get("name")
        contenu = request.form.get("contenu")
        date_debut = request.form.get("date_debut")
        date_fin = request.form.get("date_fin")
        type = request.form.get("type")
        statut = request.form.get("statut")

        if not name:
            flash("Le nom est obligatoire.", "danger")
            return render_template("html/charts/add_charts.html")
        if not contenu:
            flash("Le contenu est obligatoire.", "danger")
            return render_template("html/charts/add_charts.html")
        if not date_debut:
            flash("La date de création est obligatoire.", "danger")
            return render_template("html/charts/add_charts.html")
        if not date_fin:
                    flash("La date de création est obligatoire.", "danger")
                    return render_template("html/charts/add_charts.html")
        if not type:
            flash("Le type est obligatoire.", "danger")
            return render_template("html/charts/add_charts.html")
        if not statut:
            flash("Le statut est obligatoire.", "danger")
            return render_template("html/charts/add_charts.html")

        nouveau_rapport = Rapport_de_Compte(
            name=name,
            contenu=contenu,
            date_debut=date_debut,
            date_fin=date_fin,
            type=type,
            statut=statut,
            id_utilisateur=current_user.id
        )

        try:
            db.session.add(nouveau_rapport)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Une erreur s'est produite lors de la création du rapport.", "danger")
            return render_template("html/charts/add_charts.html")

        flash("Rapport ajouté avec succès.", "success")
        return redirect(url_for('charts'))
    return render_template("html/charts/add_charts.html")


@app.route("/charts/edit_charts.html/<int:id>", methods=["GET", "POST"])
def edit_charts(id):
    nouveau_rapport = Rapport_de_Compte.query.get_or_404(id)
    if request.method == "POST":
        nouveau_rapport.name = request.form.get("name")
        nouveau_rapport.contenu = request.form.get("contenu")
        nouveau_rapport.date_debut = request.form.get("date_debut")
        nouveau_rapport.date_fin = request.form.get("date_fin")
        nouveau_rapport.type = request.form.get("type")
        nouveau_rapport.statut = request.form.get("statut")

        db.session.commit()
        flash("Rapport mis à jour avec succès.", "success")
        return redirect(url_for("charts"))
    return render_template("html/charts/edit_charts.html", rapport=nouveau_rapport)


@app.route("/charts/charts_details/<int:id>")
def charts_details(id):
    nouveau_rapport = Rapport_de_Compte.query.get_or_404(id)
    return render_template("html/charts/charts_details.html", nouveau_rapport=nouveau_rapport)


@app.route("/delete-charts/<int:id>", methods=["POST"])
def delete_charts(id):
    charts = Rapport_de_Compte.query.get_or_404(id)
    if charts:
        db.session.delete(charts)
        db.session.commit()
        flash("Rapport supprimé avec succès.", "success")
    return redirect(url_for("charts"))


@app.route('/charts')
def charts():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)

    charts_query = Rapport_de_Compte.query
    if query:
        charts_query = charts_query.filter(
            Rapport_de_Compte.name.ilike(f'%{query}%') |
            Rapport_de_Compte.type.ilike(f'%{query}%') |
            Rapport_de_Compte.statut.ilike(f'%{query}%')
        )

    charts_page = charts_query.paginate(page=page, per_page=5, error_out=False)

    return render_template('html/charts/charts.html', charts=charts_page, q=query)



# Customers Management Routes
@app.route("/add-customer.html", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form.get("name")
        telephone = request.form.get("telephone")
        quartier = request.form.get("quartier")

        if not name:
            flash("Le nom est obligatoire.", "danger")
            return render_template("html/customers/add_customer.html")

        if not telephone:
            flash("Le numéro de téléphone est obligatoire.", "danger")
            return render_template("html/customers/add_customer.html")

        if not quartier:
            flash("Le quartier de résidence est obligatoire.", "danger")
            return render_template("html/customers/add_customer.html")

        nouveau_client = Client(
            name=name,
            numero_de_telephone=telephone,
            quartier_de_residence=quartier
        )

        try:
            db.session.add(nouveau_client)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Une erreur est survenue lors de l'enregistrement du client.", "danger")
            return render_template("html/customers/add_customer.html")

        flash("Client ajouté avec succès.", "success")
        return redirect(url_for("customers"))

    return render_template("html/customers/add_customer.html")


@app.route("/customers/edit-customer.html/<int:id_client>", methods=["GET", "POST"])
def edit_customer(id_client):
    client = Client.query.get_or_404(id_client)
    if request.method == "POST":
        client.name = request.form.get("name")
        client.numero_de_telephone = request.form.get("telephone")
        client.quartier_de_residence = request.form.get("quartier")

        db.session.commit()
        flash("Client mis à jour avec succès.", "success")
        return redirect(url_for("customers"))

    return render_template("html/customers/edit_customer.html", client=client)


@app.route("/customer-details/<int:id_client>")
def customer_details(id_client):
    client = Client.query.get_or_404(id_client)
    return render_template("html/customers/customer_details.html", client=client)


@app.route("/delete-customer/<int:id_client>", methods=["POST"])
def delete_customer(id_client):
    client = Client.query.get_or_404(id_client)
    if client:
        db.session.delete(client)
        db.session.commit()
        flash("Client supprimé avec succès.", "success")
    return redirect(url_for("customers"))

@app.route('/customers')
def customers():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)

    customers_query = Client.query
    if query:
        customers_query = customers_query.filter(
            Client.name.ilike(f'%{query}%') |
            Client.numero_de_telephone.ilike(f'%{query}%') |
            Client.quartier_de_residence.ilike(f'%{query}%')
        )

    customers_page = customers_query.paginate(page=page, per_page=5, error_out=False)

    return render_template('html/customers/customer.html', customers=customers_page, q=query)



# support route
@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        sujet = request.form.get('sujet')
        contenu = request.form.get('contenu')

        if not sujet:
            flash("Le sujet est obligatoire.", "danger")
            return render_template('html/support.html')

        if not contenu:
            flash("Le contenu est obligatoire.", "danger")
            return render_template('html/support.html')

        nouveau_commentaire = Commentaire(
            id_utilisateur=current_user.id,
            contenu=f"Sujet : {sujet}\n\n{contenu}",
            date_debut=datetime.now()
        )

        db.session.add(nouveau_commentaire)
        db.session.commit()

        flash("Votre avis compte, merci pour votre signalement.", "success")
        return redirect(url_for('index'))

    return render_template('html/support.html')

# forgot passzord route
# @app.route("/change-password", methods=["POST"])
# @login_required
# def change_password():
#     current = request.form.get("current_password")
#     new = request.form.get("new_password")
#     confirm = request.form.get("confirm_password")

#     if new != confirm:
#         flash("Les mots de passe ne correspondent pas.", "error")
#         return redirect(url_for("settings"))




#gestion des ventes et commandes 


def _lignes_commande(id_commande):
    rows = (
        db.session.query(Ligne_Commande, Produits)
        .join(Produits, Produits.id_produit == Ligne_Commande.id_produit) 
        .filter(Ligne_Commande.id_commande == id_commande)
        .all()
    )
    lignes = []
    for ligne, produit in rows:
        quantite = ligne.quantite or 0
        prix = ligne.prix_unitaire or 0
        lignes.append({
            "produit": produit.name,  # <-- À ADAPTER (name ? nom ? libelle ?)
            "quantite": quantite,
            "prix_unitaire": prix,
            "sous_total": quantite * prix,
        })
    total = sum(l["sous_total"] for l in lignes)
    return lignes, total
 
 
def _calculer_statut(attendu, percue):
    """payee / partielle / impayee, comme dans la liste des commandes."""
    if percue >= attendu and attendu > 0:
        return "payee"
    if percue > 0:
        return "partielle"
    return "impayee"

 
@app.route("/add_orders.html", methods=["GET", "POST"])
@login_required
def add_orders():
    customers = Client.query.order_by(Client.name).all()
    products = Produits.query.filter(Produits.quantite_en_stock > 0).order_by(Produits.name).all()

    if request.method == "POST":
        id_client = request.form.get("id_client", type=int)
        mode_vente = request.form.get("mode_vente")
        montant_percue = request.form.get("montant_percue", type=float) or 0
        ids_produits = request.form.getlist("id_produit")
        quantites = request.form.getlist("quantite")

        if not id_client:
            flash("Le client est obligatoire.", "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)

        if mode_vente not in ("comptant", "credit", "livraison"):
            flash("Le mode de vente est obligatoire.", "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)

        try:
            lignes = [
                {"id_produit": int(id_produit), "quantite": int(quantite)}
                for id_produit, quantite in zip(ids_produits, quantites)
                if id_produit and quantite
            ]
        except ValueError:
            flash("Les quantités doivent être des nombres entiers.", "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)

        try:
            creer_commande(
                id_client=id_client,
                lignes=lignes,
                id_utilisateur=current_user.id,
                mode_vente=mode_vente,
                montant_percue=montant_percue,
            )
        except StockInsuffisant as e:
            flash(str(e), "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)
        except IntegrityError:
            flash("Une erreur est survenue lors de l'enregistrement de la commande.", "danger")
            return render_template("html/orders/add_orders.html", customers=customers, products=products)

        flash("Commande enregistrée avec succès.", "success")
        return redirect(url_for("add_orders"))

    return render_template("html/orders/add_orders.html", customers=customers, products=products)


@app.route("/orders/<int:id_commande>")
@login_required
def orders_details(id_commande):
    commande = Commande.query.get_or_404(id_commande)
    client = Client.query.get(commande.id_client)  
    vente = Vente.query.filter_by(id_commande=id_commande).first()  
    lignes, total = _lignes_commande(id_commande)
 
    return render_template(
        "html/orders/orders_details.html",
        commande=commande,
        client=client,
        vente=vente,
        lignes=lignes,
        total=total,
    )


@app.route("/orders/<int:id_commande>/edit", methods=["GET", "POST"])
@login_required
def edit_orders(id_commande):
    commande = Commande.query.get_or_404(id_commande)
    vente = Vente.query.filter_by(id_commande=id_commande).first()  
    customers = Client.query.order_by(Client.name).all()
 
    if request.method == "POST":
        id_client = request.form.get("id_client", type=int)
        if not id_client or not Client.query.get(id_client):
            flash("Veuillez choisir un client valide.", "danger")
            return redirect(url_for("edit_orders", id_commande=id_commande))
 
        commande.id_client = id_client  
 
        if vente:
            try:
                percue = Decimal(request.form.get("montant_percue", "0") or "0")
            except InvalidOperation:
                flash("Montant perçu invalide.", "danger")
                return redirect(url_for("edit_orders", id_commande=id_commande))
 
            if percue < 0:
                flash("Le montant perçu ne peut pas être négatif.", "danger")
                return redirect(url_for("edit_orders", id_commande=id_commande))
 
            vente.montant_percue = percue
            vente.statut = _calculer_statut(Decimal(vente.montant_attendu or 0), percue)
 
        db.session.commit()
        flash("Commande modifiée avec succès.", "success")
        return redirect(url_for("orders_details", id_commande=id_commande))
 
    lignes, total = _lignes_commande(id_commande)
    return render_template(
        "html/orders/edit_orders.html",
        commande=commande,
        vente=vente,
        customers=customers,
        lignes=lignes,
        total=total,
    )


@app.route("/orders/<int:id_commande>/delete", methods=["POST"])
@login_required
def delete_orders(id_commande):
    commande = Commande.query.get_or_404(id_commande)
    try:
        lignes = Ligne_Commande.query.filter_by(id_commande=id_commande).all()
        for ligne in lignes:
            produit = product.query.get(ligne.id_produit)
            if produit:
                produit.stock += ligne.quantite 

        Vente.query.filter_by(id_commande=id_commande).delete()
        Ligne_Commande.query.filter_by(id_commande=id_commande).delete()
        db.session.delete(commande)

        db.session.commit()
        flash("Commande supprimée avec succès.", "success")
    except Exception:
        db.session.rollback()
        flash("Impossible de supprimer cette commande.", "danger")

    return redirect(url_for("orders"))


@app.route("/orders.html")
@login_required
def orders():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()

    query = (
        Commande.query
        .join(Client, Commande.id_client == Client.id_client)
        .outerjoin(Vente, Vente.id_commande == Commande.id_commande)
        .add_columns(
            Client.name.label("client_name"),
            Vente.montant_attendu.label("montant_attendu"),
            Vente.montant_percue.label("montant_percue"),
            Vente.statut.label("statut"),
            Vente.date_vente.label("date_vente"),
        )
    )
    if q:
        query = query.filter(Client.name.ilike(f"%{q}%"))

    commandes = query.order_by(Commande.id_commande.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template("html/orders/orders.html", orders=commandes, q=q)



# @app.route("/alerts.html", methods=["GET", "POST"])
# def blank():
#     return render_template("html/alerts.html")



# @app.route('/')
# def dashboard():
#     # 1. KPIs globaux issus de différents modèles
#     total_clients = Client.query.count()
#     total_commandes = Commande.query.filter(Commande.statut != 'Annulé').count()
#     chiffre_affaires = db.session.query(func.sum(Vente.prix_total)).scalar() or 0.0

#     # 2. Top produits (Jointure Vente <-> Produit)
#     top_produits_data = db.session.query(
#         product.nom, func.sum(Vente.quantite).label('total_quantite')
#     ).join(Vente).group_by(product.id).order_by(func.sum(Vente.quantite).desc()).limit(5).all()

#     # 3. Performance des Commerciaux (Jointure Commande <-> Utilisateur <-> Vente)
#     perf_commerciaux = db.session.query(
#         users.nom, func.sum(Vente.prix_total).label('ca_genere')
#     ).join(Commande, users.id == Commande.utilisateur_id)\
#      .join(Vente, Commande.id == Vente.commande_id)\
#      .group_by(users.id).all()

#     # Préparation des données pour le rendu
#     donnees = {
#         "kpis": {
#             "clients": total_clients,
#             "commandes": total_commandes,
#             "ca": round(chiffre_affaires, 2)
#         },
#         "top_produits": {
#             "labels": [p[0] for p in top_produits_data],
#             "valeurs": [p[1] for p in top_produits_data]
#         },
#         "commerciaux": {
#             "labels": [c[0] for c in perf_commerciaux],
#             "valeurs": [c[1] for c in perf_commerciaux]
#         }
#     }

#     return render_template('dashboard_complet.html', donnees=donnees)
if __name__ == '__main__':
    app.run(debug=True)