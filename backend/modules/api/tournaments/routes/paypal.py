from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from modules.database.dependencies import get_users_db
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

    # Nom acheteur depuis PayPal
    first_name = params.get("first_name", "")
    last_name = params.get("last_name", "")
    buyer_name = f"{first_name} {last_name}".strip()

    item = params.get("item_name1", "")

    # Notification Telegram
    # if not os.getenv("TEST_MODE") and os.getenv("ENV") != "dev":
    notify_user = NotifyPaymentConfirmation(
        buyer_name=buyer_name,
        product=item,
        amount=mc_gross,
    )
    notify_telegram(notify_user)

    return {"status": "success"}
