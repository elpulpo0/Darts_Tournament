from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from modules.database.dependencies import get_users_db
from modules.api.users.functions import get_current_user
from modules.api.users.models import User
from modules.api.inscriptions.models import Inscription
from modules.api.inscriptions.schemas import (
    InscriptionCreate,
    InscriptionResponse,
    InscriptionUpdate,
)
import pandas as pd
from io import BytesIO

inscription_router = APIRouter(prefix="/inscriptions", tags=["Inscriptions"])


# Fonction de dépendance pour vérifier le rôle admin (réutilisable)
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@inscription_router.post(
    "/", response_model=InscriptionResponse, status_code=status.HTTP_201_CREATED
)
def create_inscription(
    inscription: InscriptionCreate,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    # Vérifier l'unicité de la combinaison name+surname+club
    existing_inscription = (
        db.query(Inscription)
        .filter(
            Inscription.name == inscription.name,
            Inscription.surname == inscription.surname,
            Inscription.club == inscription.club,
        )
        .first()
    )
    if existing_inscription:
        raise HTTPException(
            status_code=400,
            detail="Inscription already exists for this player and club",
        )

    db_inscription = Inscription(**inscription.dict())
    db.add(db_inscription)
    db.commit()
    db.refresh(db_inscription)
    return db_inscription


@inscription_router.get("/me", response_model=InscriptionResponse)
def read_my_inscription(
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user),
):
    # Matching simple par name et surname de l'utilisateur connecté
    db_inscription = (
        db.query(Inscription)
        .filter(
            Inscription.name.ilike(current_user.name),
            Inscription.surname.ilike(current_user.surname),
        )
        .first()
    )
    if not db_inscription:
        raise HTTPException(
            status_code=404, detail="No inscription found for this user"
        )

    return db_inscription


@inscription_router.get("/{inscription_id:int}", response_model=InscriptionResponse)
def read_inscription(
    inscription_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_inscription = (
        db.query(Inscription).filter(Inscription.id == inscription_id).first()
    )
    if not db_inscription:
        raise HTTPException(status_code=404, detail="Inscription not found")
    return db_inscription


@inscription_router.put("/{inscription_id:int}", response_model=InscriptionResponse)
def update_inscription(
    inscription_id: int,
    inscription_update: InscriptionUpdate,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_inscription = (
        db.query(Inscription).filter(Inscription.id == inscription_id).first()
    )
    if not db_inscription:
        raise HTTPException(status_code=404, detail="Inscription not found")

    update_data = inscription_update.dict(exclude_unset=True)

    # Validation unicité si name, surname, club sont mis à jour
    if any(key in update_data for key in ["name", "surname", "club"]):
        new_name = update_data.get("name", db_inscription.name)
        new_surname = update_data.get("surname", db_inscription.surname)
        new_club = update_data.get("club", db_inscription.club)

        existing_inscription = (
            db.query(Inscription)
            .filter(
                Inscription.name == new_name,
                Inscription.surname == new_surname,
                Inscription.club == new_club,
                Inscription.id != inscription_id,
            )
            .first()
        )
        if existing_inscription:
            raise HTTPException(
                status_code=400,
                detail="Inscription already exists for this player and club",
            )

    for key, value in update_data.items():
        setattr(db_inscription, key, value)

    db.commit()
    db.refresh(db_inscription)
    return db_inscription


@inscription_router.get("/", response_model=List[InscriptionResponse])
def list_inscriptions(
    db: Session = Depends(get_users_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),  # Admin only
):
    inscriptions = db.query(Inscription).offset(skip).limit(limit).all()
    return inscriptions


@inscription_router.delete(
    "/{inscription_id:int}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_inscription(
    inscription_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_inscription = (
        db.query(Inscription).filter(Inscription.id == inscription_id).first()
    )
    if not db_inscription:
        raise HTTPException(status_code=404, detail="Inscription not found")

    db.delete(db_inscription)
    db.commit()
    return None


@inscription_router.post(
    "/bulk-import", response_model=Dict[str, Any], status_code=status.HTTP_200_OK
)
def bulk_import_inscriptions_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400, detail="Invalid file format: Must be Excel or CSV"
        )

    try:
        content = BytesIO(file.file.read())
        if file.filename.endswith(".csv"):
            df = pd.read_csv(content)
            sheet_name = "Sheet2"
        else:
            excel_file = pd.ExcelFile(content)
            sheet_names = excel_file.sheet_names

            if len(sheet_names) < 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"File must have at least 2 sheets. Found: {sheet_names}",
                )

            sheet_name = sheet_names[1]
            df = pd.read_excel(content, sheet_name=sheet_name, engine="openpyxl")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    df.columns = [col.strip() for col in df.columns]

    column_mapping = {
        "N": "player_number",
        "Nom": "name",
        "Prenom": "surname",
        "Club": "club",
        "Cat S": "category_simple",
        "Cat D": "category_double",
        "ND": "doublette",
    }

    df.rename(columns=column_mapping, inplace=True)

    # ✅ ARRÊTER À LA PREMIÈRE LIGNE VIDE DANS "Nom"
    first_empty_name = df[df["name"].isna() | (df["name"] == "")].index
    if len(first_empty_name) > 0:
        df = df.loc[: first_empty_name[0] - 1].reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)

    required_cols = ["name", "surname", "club"]
    missing_required = [col for col in required_cols if col not in df.columns]
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns in '{sheet_name}': {missing_required}",
        )

    # ✅ COMPTAGE AUTOMATIQUE
    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    inscriptions_to_create = []

    for idx, row in df.iterrows():
        try:
            name = str(row.get("name", "") or "").strip()
            surname = str(row.get("surname", "") or "").strip()
            club = str(row.get("club", "") or "").strip()

            if not all([name, surname, club]):
                skipped_count += 1
                continue

            # ✅ CHERCHER SI EXISTANT
            existing_inscription = (
                db.query(Inscription)
                .filter(
                    Inscription.name == name,
                    Inscription.surname == surname,
                    Inscription.club == club,
                    Inscription.date == sheet_name,
                )
                .first()
            )

            # CATEGORIE SIMPLE ET DOUBLE - SANS "nan"
            category_simple_raw = str(row.get("category_simple", "") or "").strip()
            category_double_raw = str(row.get("category_double", "") or "").strip()

            category_simple = (
                category_simple_raw
                if category_simple_raw != "nan" and category_simple_raw != ""
                else None
            )
            category_double = (
                category_double_raw
                if category_double_raw != "nan" and category_double_raw != ""
                else None
            )

            # PLAYER NUMBER
            player_number_raw = row.get("player_number")
            player_number = (
                int(player_number_raw)
                if pd.notna(player_number_raw) and str(player_number_raw).isdigit()
                else None
            )

            # DOUBLETTES (temp as player_number of partner)
            doublette_raw = row.get("doublette")
            doublette_temp = None
            if pd.notna(doublette_raw):
                doublette_str = str(doublette_raw).strip()
                if doublette_str.isdigit():
                    doublette_temp = int(doublette_str)

            # VÉRIFIER DOUBLETTES VALIDES (avec player_number)
            if doublette_temp is not None and doublette_temp > 0:
                # Trouver la ligne avec N == doublette_temp
                partner_row = df[df["player_number"] == doublette_temp]
                if partner_row.empty:
                    errors.append(
                        f"Line {idx + 2}: Invalid doublette {doublette_temp} (no matching N)"
                    )
                    continue

            if existing_inscription:
                # ✅ MISE À JOUR
                existing_inscription.category_simple = category_simple
                existing_inscription.category_double = category_double
                existing_inscription.doublette = doublette_temp  # Temp
                existing_inscription.player_number = player_number
                updated_count += 1
            else:
                # ✅ CRÉATION
                new_inscription = Inscription(
                    date=sheet_name,
                    name=name,
                    surname=surname,
                    club=club,
                    category_simple=category_simple,
                    category_double=category_double,
                    doublette=doublette_temp,  # Temp
                    player_number=player_number,
                )
                db.add(new_inscription)
                inscriptions_to_create.append(new_inscription)
                created_count += 1

        except Exception as e:
            errors.append(f"Line {idx + 2}: Error - {str(e)}")
            continue

    # ✅ COMMIT INITIAL
    db.commit()

    # ✅ RÉSOLUTION DES DOUBLETTES EN DB IDs
    # Fetch all for this date
    date_inscriptions = (
        db.query(Inscription).filter(Inscription.date == sheet_name).all()
    )

    # Map player_number to DB id
    player_to_id = {
        inc.player_number: inc.id
        for inc in date_inscriptions
        if inc.player_number is not None
    }

    # Update doublette to DB id
    for inc in date_inscriptions:
        if inc.doublette is not None:
            partner_id = player_to_id.get(inc.doublette)
            if partner_id:
                inc.doublette = partner_id
            else:
                errors.append(
                    f"Player {inc.name} {inc.surname}: Invalid doublette {inc.doublette} (no matching player_number)"
                )

    db.commit()

    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "error_count": len(errors),
        "date": sheet_name,
        "total_processed": len(df),
        "errors": errors,
        "detail": f"Bulk import completed for '{sheet_name}'",
    }


@inscription_router.delete("/", status_code=status.HTTP_200_OK)
def delete_all_inscriptions(
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),
):
    deleted_count = db.query(Inscription).delete()
    db.commit()
    return {"detail": "All inscriptions deleted", "deleted_count": deleted_count}


@inscription_router.get("/active", response_model=List[InscriptionResponse])
def list_active_inscriptions(db: Session):
    active_inscriptions = (
        db.query(Inscription)
        .filter(
            (
                (Inscription.category_simple.isnot(None))
                & (Inscription.category_simple != "nan")
                & (Inscription.category_simple != "")
            )
            | (
                (Inscription.category_double.isnot(None))
                & (Inscription.category_double != "nan")
                & (Inscription.category_double != "")
            )
        )
        .order_by(Inscription.surname, Inscription.name)
        .all()
    )
    return active_inscriptions
