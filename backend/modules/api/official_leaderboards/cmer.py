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

leaderboards_cmer_router = APIRouter(prefix="/leaderboard/cmer", tags=["CMER"])

# Path to store the parsed JSON
JSON_PATH = "official_leaderboards/cmer_leaderboard.json"


class CMEREntry(BaseModel):
    joueur: str
    oc1: str
    cc: str
    oc2: str
    oc3: str
    oc4: str
    oc5: str
    e1: str
    e2: str
    pts: str
    clt: str


class CMERCategory(BaseModel):
    category: str
    entries: List[CMEREntry]


class CMERLeaderboardResponse(BaseModel):
    leaderboard: List[CMERCategory]


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
                    if (
                        "Championnat Comité Méridional de Fléchettes - Classement"
                        in line
                    ):
                        title = line.strip()
                        break

                if title:
                    # Déterminer la catégorie depuis le titre
                    category_name = title.split("-")[-1].strip().lower()
                    if "mixte" in category_name and "individuel" in category_name:
                        current_category = "individuel_mixte"
                    elif "féminine" in category_name and "individuel" in category_name:
                        current_category = "individuel_feminin"
                    elif "vétéran" in category_name and "individuel" in category_name:
                        current_category = "individuel_veteran"
                    elif "junior" in category_name and "individuel" in category_name:
                        current_category = "individuel_junior"
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

                if len(df.columns) >= 11:  # Par sécurité (au cas où entêtes manquants)
                    df.columns = [
                        "joueur",
                        "oc1",
                        "cc",
                        "oc2",
                        "oc3",
                        "oc4",
                        "oc5",
                        "e1",
                        "e2",
                        "pts",
                        "clt",
                    ][: len(df.columns)]  # Adapter dynamiquement si colonnes en moins
                    df = df.fillna("")
                    df = df[
                        ~df["joueur"].str.contains(
                            "Total|Autre|Non|#N/A", na=False, case=False
                        )
                    ]
                    # Additional filter to exclude header row if present
                    df = df[df["joueur"] != "Joueur"]
                    df = df[df["joueur"] != "Doublette"]

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


@leaderboards_cmer_router.post("/update")
async def update_cmer_leaderboard(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_users_db),
):
    # Check if admin
    if "admin" not in current_user.scopes:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Save uploaded file temporarily
    temp_path = "temp_cmer.pdf"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        data = parse_pdf(temp_path)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return {"message": "CMER leaderboard updated successfully"}
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@leaderboards_cmer_router.get("/", response_model=CMERLeaderboardResponse)
def get_cmer_leaderboard():
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=404, detail="CMER leaderboard not yet updated")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return CMERLeaderboardResponse(**data)
