from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import pdfplumber
import pandas as pd
import json
import os
from typing import List
from pydantic import BaseModel
from collections import defaultdict
from modules.database.dependencies import get_users_db
from modules.api.users.functions import get_current_user
from sqlalchemy.orm import Session
from modules.api.users.models import User

leaderboards_lsef_router = APIRouter(prefix="/leaderboard/lsef", tags=["LSEF"])

# Path to store the parsed JSON
JSON_PATH = "leaderboards/lsef_leaderboard.json"


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


def extract_table(page):
    words = page.extract_words(keep_blank_chars=True, x_tolerance=2, y_tolerance=2)

    # Group words by approximate row (using top as key, rounded for tolerance)
    rows = defaultdict(list)
    for w in words:
        row_key = round(w["top"], 0)  # Group by approximate y-position
        rows[row_key].append(w)

    # Sort rows by y-position
    sorted_row_keys = sorted(rows.keys())

    # Find the header row containing 'Joueur'
    header_row = None
    header_y = None
    for y in sorted_row_keys:
        row_words = sorted(rows[y], key=lambda w: w["x0"])  # Sort by x-position
        texts = [w["text"] for w in row_words]
        if "Joueur" in texts:
            header_row = row_words
            header_y = y
            break

    if not header_row:
        return None

    # Define column positions based on header words' x0
    column_starts = sorted([w["x0"] for w in header_row])
    column_ends = column_starts[1:] + [page.width]

    # Header texts (including ',' for empty columns)
    header_texts = [
        w["text"].lower() for w in sorted(header_row, key=lambda w: w["x0"])
    ]

    # Map ',' to 'empty' for column names
    column_names = []
    empty_count = 0
    for h in header_texts:
        if h == "," or h == "" or h == ",,":
            empty_count += 1
            column_names.append(f"empty{empty_count}")
        else:
            column_names.append(h.replace(" ", "_"))  # e.g., 'pts_com'

    # Extract data rows (rows below header, ignoring footer)
    data = []
    page_height = page.height
    footer_threshold = page_height * 0.9  # Ignore lines in the bottom 10% of the page

    for y in sorted_row_keys:
        if y <= header_y or y >= footer_threshold:  # Skip header and footer
            continue

        row_words = rows[y]
        row_data = dict.fromkeys(column_names, "")

        for w in row_words:
            mid = (w["x0"] + w["x1"]) / 2
            for i, start in enumerate(column_starts):
                end = column_ends[i]
                if start <= mid < end:
                    row_data[column_names[i]] = w["text"]
                    break

        joueur = row_data.get("joueur", "").strip()
        if joueur and joueur != "Total Licencié":
            # Adjust for CLT > 99 shifting to PTS
            values = [
                row_data.get(col, "")
                for col in column_names
                if col not in ["joueur", "empty1", "empty2"]
            ]
            if (
                len(values) >= 3
                and values[-1].isdigit()
                and int(values[-1]) > 99
                and not values[-2].isdigit()
            ):
                # Shift CLT back to its correct position
                clt = values[-1]
                pts = values[-2] if values[-2] else "0"
                row_data["pts"] = pts
                row_data["clt"] = clt
            data.append(row_data)

    df = pd.DataFrame(data)
    # Drop empty columns
    df = df.drop(columns=[col for col in df.columns if "empty" in col], errors="ignore")
    df = df.fillna("")

    return df


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
                    elif "junior" in category_name:
                        current_category = "individuel_junior"
                    elif "mixte" in category_name and "double" in category_name:
                        current_category = "double_mixte"
                    elif "féminin" in category_name and "double" in category_name:
                        current_category = "double_feminin"
                    else:
                        current_category = None

            if current_category is None:
                continue  # Skip page if no category is currently active

            # Extract table using position-based method
            df = extract_table(page)
            if df is not None and not df.empty:
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
