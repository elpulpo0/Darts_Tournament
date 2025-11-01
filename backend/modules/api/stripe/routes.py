from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import (
    Tournament,
    TournamentPayment,
)
from modules.api.users.models import User
from modules.api.users.functions import get_current_user
from modules.api.users.telegram import notify_telegram, NotifyPaymentConfirmation
import stripe
import os
from typing import List
from modules.api.tournaments.schemas import (
    TournamentPaymentResponse,
)

# Initialise Stripe avec ta clé secrète
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


class CheckoutCreate(BaseModel):
    amount: int  # Montant en centimes, passé depuis le frontend


# Listes pour les noms en français
jours_semaine = [
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
]
mois = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def require_admin(current_user: User = Depends(get_current_user)):
    if (
        current_user.role != "admin"
    ):  # Ajusté à role basé sur votre /me (user.role.role)
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@payments_router.post("/pay_for_tournament/{tournament_id}")
async def pay_for_tournament(
    tournament_id: int,
    checkout_data: CheckoutCreate,  # Body pour recevoir l'amount depuis frontend
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user),
):
    # Récupère tournoi et user
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = checkout_data.amount  # Montant en centimes (ex: 300 pour 3€)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # Calcul des frais Stripe (1.5% + 0.25€, en centimes)
    processing_fees = int(amount * 0.015) + 25  # 0.25€ = 25 centimes
    total_amount = amount + processing_fees

    # Assumer que tournament.start_date est un objet datetime
    dt = tournament.start_date

    # Formater
    jour_semaine = jours_semaine[dt.weekday()]
    jour_mois = dt.day
    nom_mois = mois[dt.month - 1]
    annee = dt.year
    heure = dt.strftime("%H:%M")

    formatted_date = f"{jour_semaine} {jour_mois} {nom_mois} {annee} à {heure}"

    try:
        # Crée la Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],  # Carte, Apple Pay, etc.
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Tournoi: {tournament.name}",
                            "description": f"Inscription au tournoi du {formatted_date}. Inclut frais de traitement : {processing_fees / 100} €",
                        },
                        "unit_amount": total_amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",  # One-time payment
            success_url="https://badarts.fr/tournaments?success=true",
            cancel_url="https://badarts.fr/tournaments?cancel=true",
            metadata={  # Métadonnées pour webhook (récup infos user)
                "user_id": str(user.id),
                "tournament_id": str(tournament.id),
                "nickname": user.nickname,
                "name": user.name,
                "email": user.email,
            },
            customer_email=user.email,  # Prérempli pour user
        )
        return {
            "session_id": session.id,
            "url": session.url,
        }  # Renvoie URL pour redirect frontend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@payments_router.post("/tournament_webhook")
async def tournament_webhook(request: Request, db: Session = Depends(get_users_db)):
    payload = await request.body()  # Corps brut de la requête
    sig_header = request.headers.get("stripe-signature")  # Signature pour vérif
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        # Vérifie la signature (sécurité, comme IPN verify)
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Gère l'événement
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session["metadata"]

        # Récup infos user/tournoi depuis metadata
        user_id = int(metadata.get("user_id"))
        tournament_id = int(metadata.get("tournament_id"))
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            buyer_name = user.name if user.name else user.nickname

        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        amount = session["amount_total"] / 100  # En € (ex: 3.0)
        product = tournament.name

        # Mise à jour de la base de données : Créer ou mettre à jour l'entrée TournamentPayment
        payment = (
            db.query(TournamentPayment)
            .filter(
                TournamentPayment.user_id == user_id,
                TournamentPayment.tournament_id == tournament_id,
            )
            .first()
        )

        if not payment:
            payment = TournamentPayment(
                user_id=user_id, tournament_id=tournament_id, paid=True
            )
            db.add(payment)
        else:
            payment.paid = True

        db.commit()

        # Envoie notification Telegram
        if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
            notify_user = NotifyPaymentConfirmation(
                buyer_name=buyer_name,
                product=product,
                amount=amount,
            )
            notify_telegram(notify_user)

    return {"status": "success"}


@payments_router.get("/check/{tournament_id}", response_model=dict)
async def check_payment(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user),
):
    payment = (
        db.query(TournamentPayment)
        .filter(
            TournamentPayment.user_id == current_user.id,
            TournamentPayment.tournament_id == tournament_id,
        )
        .first()
    )
    if not payment:
        return {"paid": False}
    return {"paid": payment.paid}


@payments_router.delete("/{tournament_id}/{user_id}")
async def delete_payment(
    tournament_id: int,
    user_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),
):
    payment = (
        db.query(TournamentPayment)
        .filter(
            TournamentPayment.user_id == user_id,
            TournamentPayment.tournament_id == tournament_id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}


@payments_router.get("/{tournament_id}", response_model=List[TournamentPaymentResponse])
async def list_payments(
    tournament_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),
):
    payments = (
        db.query(TournamentPayment)
        .filter(TournamentPayment.tournament_id == tournament_id)
        .all()
    )
    return payments
