from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from modules.database.dependencies import get_users_db
from modules.api.tournaments.models import (
    Tournament,
)
from modules.api.users.models import User
from modules.api.users.telegram import notify_telegram, NotifyPaymentConfirmation

import requests
from fastapi import Request

from utils.logger_config import configure_logger

logger = configure_logger()

paypal_router = APIRouter(prefix="/paypal", tags=["Paypal IPN"])


@paypal_router.post(
    "/ipn",
    status_code=status.HTTP_200_OK,
    summary="PayPal IPN Handler",
    description="Handles PayPal Instant Payment Notifications (IPN) for tournament payments.",
)
async def paypal_ipn_handler(request: Request, db: Session = Depends(get_users_db)):
    # Lire les données POST
    form_data = await request.form()
    params = dict(form_data)

    # Vérifier l'IPN
    verify_url = "https://ipnpb.paypal.com/cgi-bin/webscr"
    # verify_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    post_data = {**params, "cmd": "_notify-validate"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(verify_url, data=post_data, headers=headers)

    if response.text != "VERIFIED":
        logger.error(f"IPN invalide: {response.text}")
        raise HTTPException(status_code=400, detail="Invalid IPN")

    # Vérifier statut paiement
    payment_status = params.get("payment_status", "")
    if payment_status != "Completed":
        logger.info(f"Paiement non complété: {payment_status}")
        return {"status": "ignored"}

    # Vérifier receiver (sécurité basique)
    expected_receiver = "badarts34@gmail.com"
    receiver_email = params.get("receiver_email", "").lower()
    business = params.get("business", "").lower()
    if receiver_email != expected_receiver and business != expected_receiver:
        logger.error("Receiver mismatch")
        raise HTTPException(status_code=400, detail="Invalid receiver")

    # Récupérer montant
    mc_gross = float(params.get("mc_gross", 0))

    # Parser custom
    custom = params.get("custom", "")
    if not custom:
        raise HTTPException(status_code=400, detail="Missing custom data")

    custom_parts = custom.split(",")
    user_id = int(custom_parts[0].split(":")[1]) if len(custom_parts) > 0 else None
    tournament_id = (
        int(custom_parts[1].split(":")[1]) if len(custom_parts) > 1 else None
    )

    if not user_id or not tournament_id:
        raise HTTPException(status_code=400, detail="Invalid custom format")

    # Récupérer user et tournament
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Nom acheteur depuis PayPal
    first_name = params.get("first_name", "")
    last_name = params.get("last_name", "")
    buyer_name = f"{first_name} {last_name}".strip() or user.nickname

    # Notification Telegram
    # if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
    notify_user = NotifyPaymentConfirmation(
        buyer_name=buyer_name,
        product=tournament.name,
        amount=mc_gross,
    )
    notify_telegram(notify_user)

    return {"status": "success"}
