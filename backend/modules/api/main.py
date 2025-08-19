from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from modules.api.users.create_db import init_users_db
from modules.api.users.routes import users_router
from modules.api.auth.routes import auth_router
from modules.api.notifs.routes import notifs_router
from modules.api.admin.db_admin import router as admin_router
from modules.api.tournaments.routes import tournaments_router
from scheduler import start_scheduler


import os
from dotenv import load_dotenv

load_dotenv()

PORT_FRONT = os.getenv("PORT_FRONT")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Badarts API",
        description="API for the Badarts apps administration dashboard",
        version="1.2.0",
    )

    # Ajout du middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{PORT_FRONT}",
            f"http://77.37.51.76:{PORT_FRONT}",
            "https://badarts.fr",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter()
    router.include_router(auth_router, prefix="/auth", tags=["Authentification"])
    router.include_router(users_router, prefix="/users", tags=["Users"])
    router.include_router(notifs_router, tags=["Notifications"])
    router.include_router(tournaments_router, tags=["Tournaments"])
    router.include_router(admin_router)

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Initialisation safe de la DB
    init_users_db()

    start_scheduler()

    return app


app = create_app()
