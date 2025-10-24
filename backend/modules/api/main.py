from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import HTTPException, Path
from pydantic import BaseModel
import os
import requests
from typing import List, Any

from modules.api.users.create_db import init_users_db
from modules.api.users.routes import users_router
from modules.api.auth.routes import auth_router
from modules.api.notifs.routes import notifs_router
from modules.api.admin.db_admin import router as admin_router
from modules.api.tournaments.routes.leaderboards import leaderboards_router
from modules.api.tournaments.routes.matches import matches_router
from modules.api.tournaments.routes.pools import pools_router
from modules.api.tournaments.routes.tournaments import tournaments_router
from modules.api.calendar.routes import calendar_router
from modules.api.official_leaderboards.lsef import leaderboards_lsef_router
from modules.api.official_leaderboards.cmer import leaderboards_cmer_router
from modules.api.licences.routes import licence_router
from modules.api.inscriptions.routes import inscription_router
from scheduler import start_scheduler


import os
from dotenv import load_dotenv

load_dotenv()

PORT_FRONT = os.getenv("PORT_FRONT")


# Printful setup (ajouté pour l'intégration)
PRINTFUL = os.getenv("PRINTFUL")
STORE_ID = "badarts"  # Hardcodé ou via config

if not PRINTFUL:
    print("⚠️ PRINTFUL manquant dans env vars – les routes Printful seront désactivées.")

BASE_URL = "https://api.printful.com"

# Models pour validation (optionnel, mais clean)
class OrderData(BaseModel):
    recipient: dict
    items: List[dict]

# Dependency pour headers Printful (réutilisable)
def get_printful_headers() -> dict:
    return {
        "Authorization": f"Bearer {PRINTFUL}",
        "X-PF-Store-Id": STORE_ID,
        "Content-Type": "application/json"
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="Badarts API",
        description="API for the Badarts apps administration dashboard",
        version="1.2.0",
    )

    # Ajout du middleware CORS (inchangé)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{PORT_FRONT}",
            f"http://77.37.51.76:{PORT_FRONT}",
            "https://www.badarts.fr",
            "https://badarts.fr",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter()

    # Routes existantes (inchangées)
    router.include_router(auth_router, prefix="/auth", tags=["Authentification"])
    router.include_router(users_router, prefix="/users", tags=["Users"])
    router.include_router(notifs_router, tags=["Notifications"])
    router.include_router(tournaments_router)
    router.include_router(leaderboards_router)
    router.include_router(pools_router)
    router.include_router(matches_router)
    router.include_router(leaderboards_lsef_router)
    router.include_router(leaderboards_cmer_router)
    router.include_router(calendar_router)
    router.include_router(licence_router)
    router.include_router(inscription_router)

    router.include_router(admin_router)

    # NOUVEAU : Router Printful (intégration boutique)
    printful_router = APIRouter(prefix="/api/printful", tags=["Printful Boutique"])

    @printful_router.get("/store/products", response_model=dict)
    async def get_store_products():
        if not PRINTFUL:
            raise HTTPException(status_code=500, detail="PRINTFUL manquant")
        try:
            response = requests.get(
                f"{BASE_URL}/store/products",
                headers=get_printful_headers()
            )
            response.raise_for_status()
            data = response.json()
            return data  # { "code": 200, "result": [...] }
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Erreur API Printful: {str(e)}")

    @printful_router.get("/store/products/{product_id}", response_model=dict)
    async def get_store_product(product_id: int = Path(..., description="ID du produit")):
        if not PRINTFUL:
            raise HTTPException(status_code=500, detail="PRINTFUL manquant")
        try:
            response = requests.get(
                f"{BASE_URL}/store/products/{product_id}",
                headers=get_printful_headers()
            )
            response.raise_for_status()
            data = response.json()
            return data
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
                json=order_data.dict()  # { recipient: {...}, items: [...] }
            )
            response.raise_for_status()
            data = response.json()
            return data  # { "code": 200, "result": { id: ..., ... } }
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Erreur commande Printful: {str(e)}")

    # Health check Printful (optionnel)
    @printful_router.get("/health")
    async def printful_health():
        return {"status": "ok", "PRINTFUL_set": bool(PRINTFUL)}

    # Inclusion du router Printful
    router.include_router(printful_router)

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Initialisation safe de la DB (inchangée)
    init_users_db()

    start_scheduler()

    return app


app = create_app()