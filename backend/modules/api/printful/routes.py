from fastapi import APIRouter, Path, HTTPException, Body
from typing import List
from pydantic import BaseModel
import os
import requests

printful_router = APIRouter(prefix="/api/printful", tags=["Printful Boutique"])

PRINTFUL = os.getenv("PRINTFUL")
STORE_ID = "badarts"

if not PRINTFUL:
    print("⚠️ PRINTFUL manquant dans env vars – les routes Printful seront désactivées.")

BASE_URL = "https://api.printful.com"


# Models for validation
class OrderData(BaseModel):
    recipient: dict
    items: List[dict]
    confirm: bool = False
    external_id: str | None = None


class ConfirmOrderData(BaseModel):
    external_id: str | None = None


class ShippingRateData(BaseModel):
    recipient: dict
    items: List[dict]


# Dependency for Printful headers
def get_printful_headers() -> dict:
    return {
        "Authorization": f"Bearer {PRINTFUL}",
        "X-PF-Store-Id": STORE_ID,
        "Content-Type": "application/json",
    }


@printful_router.get("/store/products", response_model=dict)
async def get_store_products():
    if not PRINTFUL:
        raise HTTPException(status_code=500, detail="PRINTFUL manquant")
    try:
        response = requests.get(
            f"{BASE_URL}/store/products", headers=get_printful_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur API Printful: {str(e)}")


@printful_router.get("/store/products/{product_id}", response_model=dict)
async def get_store_product(product_id: int = Path(..., description="ID du produit")):
    if not PRINTFUL:
        raise HTTPException(status_code=500, detail="PRINTFUL manquant")
    try:
        response = requests.get(
            f"{BASE_URL}/store/products/{product_id}",
            headers=get_printful_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur API Printful: {str(e)}")


@printful_router.post("/orders", response_model=dict)
async def create_order(order_data: OrderData):
    if not PRINTFUL:
        raise HTTPException(status_code=500, detail="PRINTFUL manquant")
    try:
        response = requests.post(
            f"{BASE_URL}/orders",
            headers=get_printful_headers(),
            json=order_data.dict(exclude_none=True),
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur commande Printful: {str(e)}"
        )


@printful_router.post("/orders/{order_id}/confirm", response_model=dict)
async def confirm_order(
    order_id: int = Path(..., description="ID de la commande"),
    confirm_data: ConfirmOrderData = Body(...),
):
    if not PRINTFUL:
        raise HTTPException(status_code=500, detail="PRINTFUL manquant")
    try:
        response = requests.post(
            f"{BASE_URL}/orders/{order_id}/confirm",
            headers=get_printful_headers(),
            json=confirm_data.dict(exclude_none=True),
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur confirmation commande Printful: {str(e)}"
        )


@printful_router.get("/health")
async def printful_health():
    return {"status": "ok", "PRINTFUL_set": bool(PRINTFUL)}
