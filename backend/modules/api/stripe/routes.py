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

# Initialise Stripe avec ta clé secrète
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


class CheckoutCreate(BaseModel):
    amount: int  # Montant en centimes, passé depuis le frontend


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

    amount = checkout_data.amount
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    try:
        # Crée la Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],  # Carte, Apple Pay, etc.
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Inscription Tournoi: {tournament.name}",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",  # One-time payment
            success_url="https://badarts.fr/tournaments",
            cancel_url="https://badarts.fr/tournaments",
            # success_url="https://badarts.fr/tournaments?success=true&session_id={CHECKOUT_SESSION_ID}",
            # cancel_url="https://badarts.fr/tournaments?cancel=true",
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
