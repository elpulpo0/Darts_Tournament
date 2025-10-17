from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from modules.database.dependencies import get_users_db
from modules.api.users.functions import get_current_user
from modules.api.licences.models import Licence
from modules.api.users.models import User
from modules.api.licences.schemas import LicenceCreate, LicenceResponse, LicenceUpdate
import pandas as pd
from io import BytesIO
from fuzzywuzzy import fuzz, process
from sqlalchemy.exc import IntegrityError

licence_router = APIRouter(prefix="/licences", tags=["licences"])


# Fonction de dépendance pour vérifier le rôle admin (réutilisable)
def require_admin(current_user: User = Depends(get_current_user)):
    if (
        current_user.role != "admin"
    ):  # Ajusté à role basé sur votre /me (user.role.role)
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@licence_router.post(
    "/", response_model=LicenceResponse, status_code=status.HTTP_201_CREATED
)
def create_licence(
    licence: LicenceCreate,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    # Validation : Vérifier que l'user_id existe (pour respecter la FK et éviter IntegrityError)
    user_exists = db.query(User).filter(User.id == licence.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=400, detail="Invalid user_id: User not found")

    # Vérifier l'unicité du licence_number si besoin (ex: assumé unique dans votre contexte)
    existing_licence = (
        db.query(Licence)
        .filter(Licence.licence_number == licence.licence_number)
        .first()
    )
    if existing_licence:
        raise HTTPException(status_code=400, detail="Licence number already exists")

    db_licence = Licence(**licence.dict())
    db.add(db_licence)
    db.commit()
    db.refresh(db_licence)
    return db_licence


@licence_router.get("/me", response_model=LicenceResponse)
def read_my_licence(
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user),
):
    # Récupérer la licence liée à current_user.id
    db_licence = db.query(Licence).filter(Licence.user_id == current_user.id).first()
    if not db_licence:
        raise HTTPException(status_code=404, detail="No licence found for this user")

    return db_licence


@licence_router.get("/{licence_id:int}", response_model=LicenceResponse)
def read_licence(
    licence_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_licence = db.query(Licence).filter(Licence.id == licence_id).first()
    if not db_licence:
        raise HTTPException(status_code=404, detail="Licence not found")
    return db_licence


@licence_router.put("/{licence_id:int}", response_model=LicenceResponse)
def update_licence(
    licence_id: int,
    licence_update: LicenceUpdate,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_licence = db.query(Licence).filter(Licence.id == licence_id).first()
    if not db_licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    update_data = licence_update.dict(exclude_unset=True)

    # Validation si user_id est mis à jour
    if "user_id" in update_data:
        user_exists = db.query(User).filter(User.id == update_data["user_id"]).first()
        if not user_exists:
            raise HTTPException(
                status_code=400, detail="Invalid user_id: User not found"
            )

    # Validation unicité pour licence_number si mis à jour
    if "licence_number" in update_data:
        existing_licence = (
            db.query(Licence)
            .filter(
                Licence.licence_number == update_data["licence_number"],
                Licence.id != licence_id,
            )
            .first()
        )
        if existing_licence:
            raise HTTPException(status_code=400, detail="Licence number already exists")

    for key, value in update_data.items():
        setattr(db_licence, key, value)

    db.commit()
    db.refresh(db_licence)
    return db_licence


@licence_router.get("/", response_model=List[LicenceResponse])
def list_licences(
    db: Session = Depends(get_users_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),  # Admin only
):
    licences = db.query(Licence).offset(skip).limit(limit).all()
    return licences


@licence_router.delete("/{licence_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_licence(
    licence_id: int,
    db: Session = Depends(get_users_db),
    current_user: User = Depends(require_admin),  # Admin only
):
    db_licence = db.query(Licence).filter(Licence.id == licence_id).first()
    if not db_licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    db.delete(db_licence)
    db.commit()
    return None


@licence_router.post(
    "/bulk-create", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED
)
def bulk_create_licences_from_excel(
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
        else:
            df = pd.read_excel(content, engine="openpyxl")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    df.columns = [col.strip() for col in df.columns]
    column_mapping = {}
    for col in df.columns:
        if col == "Cat.":
            column_mapping[col] = "Cat. Club"
        else:
            column_mapping[col] = col
    df.rename(columns=column_mapping, inplace=True)

    required_cols = [
        "LIG",
        "COM",
        "N° Club",
        "Club",
        "NOM",
        "Prénom",
        "Licence",
        "Cat. Club",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing or mismatched columns. Expected: {required_cols}. Found: {list(df.columns)}. Missing: {missing_cols}",
        )

    all_users_raw = db.query(User).all()
    valid_users = [user for user in all_users_raw if user.name and user.name.strip()]
    if not valid_users:
        raise HTTPException(
            status_code=500, detail="No valid users with name in database for matching"
        )

    valid_user_names = [user.name.lower().strip() for user in valid_users]
    user_name_to_id_valid = {user.name.lower().strip(): user.id for user in valid_users}

    success_count = 0
    errors = []
    licences_to_create = []

    existing_licence_numbers = {
        lic.licence_number for lic in db.query(Licence.licence_number).all()
    }

    for idx, row in df.iterrows():
        try:
            ligue = str(row.get("LIG", "") or "").strip()
            comite = str(row.get("COM", "") or "").strip()
            club_number_raw = row.get("N° Club")
            club_number = (
                int(club_number_raw) if club_number_raw not in (None, "", "nan") else 0
            )
            club_name = str(row.get("Club", "") or "").strip()
            name_lic = str(row.get("NOM", "") or "").strip()
            surname = str(row.get("Prénom", "") or "").strip()
            category = str(row.get("Cat. Club", "") or "").strip()
            licence_number_raw = row.get("Licence")
            licence_number = (
                int(licence_number_raw)
                if licence_number_raw not in (None, "", "nan")
                else 0
            )

            if not all(
                [
                    ligue,
                    comite,
                    club_number,
                    club_name,
                    name_lic or surname,
                    category,
                    licence_number,
                ]
            ):
                errors.append(f"Line {idx + 2}: Missing required fields in row")
                continue

            if licence_number in existing_licence_numbers:
                errors.append(
                    f"Line {idx + 2}: Licence number {licence_number} already exists"
                )
                continue

            search_key = f"{surname} {name_lic}".strip().lower()
            if not search_key:
                errors.append(
                    f"Line {idx + 2}: No name/surname provided for user matching"
                )
                continue

            user_id = user_name_to_id_valid.get(search_key)
            if not user_id:
                best_match, score = process.extractOne(
                    search_key,
                    valid_user_names,
                    scorer=fuzz.token_sort_ratio,
                )
                if score < 85:
                    errors.append(
                        f"Line {idx + 2}: No matching user for '{search_key}' (best: {best_match}, score: {score})"
                    )
                    continue
                user_id = user_name_to_id_valid.get(best_match)

            if not user_id:
                errors.append(
                    f"Line {idx + 2}: Failed to resolve user_id for '{search_key}'"
                )
                continue

            licences_to_create.append(
                Licence(
                    ligue=ligue,
                    comite=comite,
                    club_number=club_number,
                    club_name=club_name,
                    name=name_lic,
                    surname=surname,
                    category=category,
                    licence_number=licence_number,
                    user_id=user_id,
                )
            )
            existing_licence_numbers.add(licence_number)
            success_count += 1

        except Exception as e:
            errors.append(f"Line {idx + 2}: Error processing row - {str(e)}")
            continue

    if licences_to_create:
        try:
            db.add_all(licences_to_create)
            db.commit()
            for lic in licences_to_create:
                db.refresh(lic)
        except IntegrityError as e:
            db.rollback()
            errors.append(f"Database integrity error during bulk insert: {str(e)}")
            success_count = 0

    return {
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors,
        "detail": "Bulk creation completed",
    }
