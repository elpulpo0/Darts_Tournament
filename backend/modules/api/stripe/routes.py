from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import Tournament
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


@payments_router.post("/create-checkout-session/{tournament_id}")
async def create_checkout_session(
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

    # Montant passé depuis le frontend (ex: fees[tournament_id] * 100)
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
            success_url="https://badarts.fr/tournaments?success=true&session_id={CHECKOUT_SESSION_ID}",  # Remplace par ton domaine réel
            cancel_url="https://badarts.fr/tournaments?cancel=true",  # Remplace par ton domaine réel
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


@payments_router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_users_db)):
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
        buyer_name = metadata.get("nickname", "Inconnu")  # Ou full name si ajouté

        # Optionnel: Query DB pour plus d'infos user (ex: si metadata incomplet)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            buyer_name = (
                user.name or buyer_name
            )  # Utilise name si dispo, fallback nickname
            # Ajoute d'autres infos si needed (ex: email = user.email)

        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        amount = session["amount_total"] / 100  # En € (ex: 3.0)
        product = (
            tournament.name
        )  # Ou session['display_items'][0]['custom']['name'] si customisé

        # Envoie notification Telegram
        # if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
        notify_user = NotifyPaymentConfirmation(
            buyer_name=buyer_name,
            product=product,
            amount=amount,
        )
        notify_telegram(notify_user)

    return {"status": "success"}
