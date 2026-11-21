from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.financial_intelligence import generate_financial_insights

router = APIRouter(
    prefix="/api/insights",
    tags=["Financial Intelligence"]
)


@router.get("/{user_id}")
def get_financial_insights(
    user_id: str,
    db: Session = Depends(get_db)
):
    result = generate_financial_insights(db, user_id)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result