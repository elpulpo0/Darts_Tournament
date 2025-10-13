from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import pdfplumber
import pandas as pd
import json
import os
from typing import List
from pydantic import BaseModel
from modules.database.dependencies import get_users_db
from modules.api.users.functions import get_current_user
from sqlalchemy.orm import Session
from modules.api.users.models import User

leaderboards_lsef_router = APIRouter(prefix="/leaderboard/lsef", tags=["LSEF"])

# Path to store the parsed JSON
JSON_PATH = "official_leaderboards/lsef_leaderboard.json"


class LSEFEntry(BaseModel):
    joueur: str
    ol1: str
    ol2: str
    ol3: str
    cl: str
    ol4: str
    e1: str
    e2: str
    master: str
    pts_com: str
    pts: str
    clt: str


class LSEFCategory(BaseModel):
    category: str
    entries: List[LSEFEntry]


class LSEFLeaderboardResponse(BaseModel):
    leaderboard: List[LSEFCategory]


def parse_pdf(file_path: str) -> dict:
    categories = {}
    current_category = None

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            title = None
            if text:
                lines = text.split("\n")
                for line in lines:
                    if "Championnat Ligue Sud-Est de Fléchettes - Classement" in line:
                        title = line.strip()
                        break

                if title:
                    # Déterminer la catégorie depuis le titre
                    category_name = title.split("-")[-1].strip().lower()
                    if "mixte" in category_name and "individuel" in category_name:
                        current_category = "individuel_mixte"
                    elif "féminin" in category_name and "individuel" in category_name:
                        current_category = "individuel_feminin"
                    elif "vétéran" in category_name:
                        current_category = "individuel_veteran"
                    elif "mixte" in category_name and "double" in category_name:
                        current_category = "double_mixte"
                    elif "féminin" in category_name and "double" in category_name:
                        current_category = "double_feminin"
                    else:
                        current_category = None

            if current_category is None:
                continue  # Skip page if no category is currently active

            # Extraire les tableaux
            tables = page.extract_tables()
            if tables:
                table = tables[0]  # Suppose un seul tableau par page
                df = pd.DataFrame(table[1:], columns=table[0])

                # Nettoyage
                df = df.dropna(subset=[df.columns[0]])
                df = df[df[df.columns[0]].str.strip() != ""]

                if len(df.columns) >= 12:  # Par sécurité (au cas où entêtes manquants)
                    df.columns = [
                        "joueur",
                        "ol1",
                        "ol2",
                        "ol3",
                        "cl",
                        "ol4",
                        "e1",
                        "e2",
                        "empty1",
                        "master",
                        "pts_com",
                        "empty2",
                        "pts",
                        "clt",
                    ][: len(df.columns)]  # Adapter dynamiquement si colonnes en moins
                    df = df.fillna("")

                    # Supprimer les colonnes inutiles si elles existent
                    df = df.drop(columns=["empty1", "empty2"], errors="ignore")

                    df = df[~df["joueur"].str.contains("Total Licencié", na=False)]

                    if current_category in categories:
                        categories[current_category] = pd.concat(
                            [categories[current_category], df], ignore_index=True
                        )
                    else:
                        categories[current_category] = df

    # Préparation de la réponse
    leaderboard = []
    for cat, df in categories.items():
        leaderboard.append({"category": cat, "entries": df.to_dict(orient="records")})

    return {"leaderboard": leaderboard}


@leaderboards_lsef_router.post("/update")
async def update_lsef_leaderboard(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    # Check if admin
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Save uploaded file temporarily
    temp_path = "temp_lsef.pdf"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        data = parse_pdf(temp_path)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return {"message": "LSEF leaderboard updated successfully"}
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@leaderboards_lsef_router.get("/", response_model=LSEFLeaderboardResponse)
def get_lsef_leaderboard():
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=404, detail="LSEF leaderboard not yet updated")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return LSEFLeaderboardResponse(**data)
