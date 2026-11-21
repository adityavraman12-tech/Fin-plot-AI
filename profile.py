from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FinancialProfile
from app.schemas.profile import (
    FinancialProfileCreate,
    FinancialProfileResponse,
)

router = APIRouter(
    prefix="/api/profile",
    tags=["Financial Profile"]
)


@router.post("/", response_model=FinancialProfileResponse)
def create_profile(profile: FinancialProfileCreate, db: Session = Depends(get_db)):

    existing = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == profile.user_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists")

    new_profile = FinancialProfile(**profile.model_dump())

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@router.get("/{user_id}", response_model=FinancialProfileResponse)
def get_profile(user_id: str, db: Session = Depends(get_db)):

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.put("/{user_id}", response_model=FinancialProfileResponse)
def update_profile(
    user_id: str,
    profile_data: FinancialProfileCreate,
    db: Session = Depends(get_db)
):

    if profile_data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in profile_data.model_dump().items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return profile