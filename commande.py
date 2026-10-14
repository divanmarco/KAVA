from datetime import datetime
from decimal import Decimal
from extensions import db
from models import Client, Produits, Commande, Ligne_Commande, Vente, Versement


class StockInsuffisant(Exception):
    """Levée quand le stock ne permet pas de vendre la quantité demandée."""


def creer_commande(id_client, lignes, id_utilisateur):
    """Crée une commande et ses lignes. La vente (paiement) se fait ensuite
    avec vendre_commande(). Le stock est réservé dès la commande."""
    if not lignes:
        raise ValueError("La commande est vide.")

    client = db.session.get(Client, id_client)
    if client is None:
        raise ValueError("Client introuvable.")

    try:
        commande = Commande(id_client=id_client, name=f"Commande {client.name}"[:50])
        db.session.add(commande)
        db.session.flush()  # obtient id_commande sans encore valider

        for ligne in lignes:
            quantite = int(ligne["quantite"])
            if quantite <= 0:
                raise ValueError("La quantité doit être supérieure à 0.")

            type_vente = ligne.get("type_vente", "unite")
            if type_vente not in ("unite", "bloc"):
                raise ValueError("Type de vente invalide.")

            # verrou : évite que deux requêtes lisent le même stock en même temps
            produit = db.session.get(Produits, ligne["id_produit"], with_for_update=True)
            if produit is None:
                raise ValueError(f"Produit {ligne['id_produit']} introuvable.")

            if type_vente == "bloc":
                if not produit.prix_bloc or not produit.unite_par_bloc:
                    raise ValueError(
                        f"« {produit.name} » n'a pas de prix carton défini."
                    )
                prix = produit.prix_bloc
                unites = quantite * produit.unite_par_bloc
            else:
                prix = produit.prix_de_vente
                unites = quantite

            if produit.quantite_en_stock < unites:
                raise StockInsuffisant(
                    f"Stock insuffisant pour « {produit.name} » : "
                    f"{produit.quantite_en_stock} unité(s) disponible(s), {unites} demandée(s)."
                )

            produit.quantite_en_stock -= unites
            if produit.quantite_en_stock == 0:
                produit.status = "Épuisé"

            db.session.add(Ligne_Commande(
                id_commande=commande.id_commande,
                id_produit=produit.id_produit,
                name=produit.name[:50],
                quantite=quantite,
                type_vente=type_vente,
                prix_unitaire=prix,
            ))

        db.session.commit()
        return commande.id_commande

    except Exception:
        db.session.rollback()
        raise


def total_commande(id_commande):
    lignes = Ligne_Commande.query.filter_by(id_commande=id_commande).all()
    return sum((l.quantite * l.prix_unitaire for l in lignes), Decimal("0"))


def vendre_commande(id_commande, id_utilisateur, mode_vente, montant_percue=0):
    """Enregistre la vente (paiement + action à mener) d'une commande existante."""
    commande = db.session.get(Commande, id_commande)
    if commande is None:
        raise ValueError("Commande introuvable.")
    if Vente.query.filter_by(id_commande=id_commande).first():
        raise ValueError("Cette commande a déjà été vendue.")
    if mode_vente not in ("a_servir", "a_livrer"):
        raise ValueError("L'action à mener est obligatoire.")

    montant_percue = Decimal(str(montant_percue or 0))
    if montant_percue < 0:
        raise ValueError("Le montant perçu ne peut pas être négatif.")

    total = total_commande(id_commande)
    if montant_percue >= total:
        statut = "payee"
    elif montant_percue > 0:
        statut = "partielle"
    else:
        statut = "impayee"

    try:
        vente = Vente(
            id_commande=id_commande,
            montant_percue=montant_percue,
            montant_attendu=total,
            statut=statut,
            mode_vente=mode_vente,
            id_utilisateur=id_utilisateur,
            date_vente=datetime.now(),
        )
        db.session.add(vente)
        db.session.flush()  # obtient id_vente
        if montant_percue > 0:
            # premier versement : une ligne d'historique qu'on ne modifie jamais
            db.session.add(Versement(
                id_vente=vente.id_vente,
                montant=montant_percue,
                date_versement=datetime.now(),
                id_utilisateur=id_utilisateur,
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def completer_paiement(id_commande, montant, id_utilisateur):
    """Ajoute un versement à une vente partielle ou impayée (sans toucher à la commande)."""
    vente = (Vente.query.filter_by(id_commande=id_commande)
             .with_for_update().first())
    if vente is None:
        raise ValueError("Cette commande n'a pas encore été vendue.")
    if vente.statut == "payee":
        raise ValueError("Cette commande est déjà entièrement payée.")

    montant = Decimal(str(montant or 0))
    if montant <= 0:
        raise ValueError("Le montant doit être supérieur à 0.")

    reste = vente.montant_attendu - vente.montant_percue
    if montant > reste:
        raise ValueError(f"Le montant dépasse le reste à payer ({reste}).")

    try:
        vente.montant_percue += montant
        db.session.add(Versement(
            id_vente=vente.id_vente,
            montant=montant,
            date_versement=datetime.now(),
            id_utilisateur=id_utilisateur,
        ))
        vente.statut = "payee" if vente.montant_percue >= vente.montant_attendu else "partielle"
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
