from datetime import datetime
from decimal import Decimal
from extensions import db
from models import Client, Produits, Commande, Ligne_Commande, Vente  


class StockInsuffisant(Exception):
    """Levée quand le stock ne permet pas de vendre la quantité demandée."""


def creer_commande(id_client, lignes, id_utilisateur, mode_vente="comptant", montant_percue=0):
   
    if not lignes:
        raise ValueError("La commande est vide.")

    client = db.session.get(Client, id_client)
    if client is None:
        raise ValueError("Client introuvable.")

    try:
        commande = Commande(id_client=id_client, name=f"Commande {client.name}"[:50])
        db.session.add(commande)
        db.session.flush()  # obtient id_commande sans encore valider

        total = Decimal("0")

        for ligne in lignes:
            quantite = int(ligne["quantite"])
            if quantite <= 0:
                raise ValueError("La quantité doit être supérieure à 0.")

            # with_for_update verrouille la ligne du produit pendant la vente
            produit = db.session.get(Produits, ligne["id_produit"], with_for_update=True)
            if produit is None:
                raise ValueError(f"Produit {ligne['id_produit']} introuvable.")

            if produit.quantite_en_stock < quantite:
                raise StockInsuffisant(
                    f"Stock insuffisant pour « {produit.name} » : "
                    f"{produit.quantite_en_stock} disponible(s), {quantite} demandé(s)."
                )

            produit.quantite_en_stock -= quantite
            if produit.quantite_en_stock == 0:
                produit.status = "Épuisé"

            db.session.add(Ligne_Commande(
                id_commande=commande.id_commande,
                id_produit=produit.id_produit,
                name=produit.name[:50],
                quantite=quantite,
                prix_unitaire=produit.prix_de_vente,
            ))
            total += produit.prix_de_vente * quantite

        montant_percue = Decimal(str(montant_percue))
        if montant_percue >= total:
            statut = "payee"
        elif montant_percue > 0:
            statut = "partielle"
        else:
            statut = "impayee"

        db.session.add(Vente(
            id_commande=commande.id_commande,
            montant_percue=montant_percue,
            montant_attendu=total,
            statut=statut,
            mode_vente=mode_vente,
            id_utilisateur=id_utilisateur,
            date_vente=datetime.now(),
        ))

        db.session.commit()
        return commande.id_commande

    except Exception:
        db.session.rollback()
        raise