from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Transaction, FinancialProfile
from app.services.ai_copilot import ask_financial_copilot
from app.auth import get_current_user

router = APIRouter(prefix="/api/copilot", tags=["AI Financial Copilot"])


@router.post("/ask")
def ask_copilot(
    question: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user["id"]

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == user_id
    ).first()

    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.transaction_date.desc()).limit(100).all()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Financial profile not found"
        )

    financial_context = {
        "monthly_income": profile.monthly_income,
        "monthly_fixed_expenses": profile.monthly_fixed_expenses,
        "current_savings": profile.current_savings,
        "emergency_fund": profile.emergency_fund,
        "financial_goal": profile.financial_goal,
        "goal_amount": profile.goal_amount,
        "goal_deadline": str(profile.goal_deadline),
        "recent_transactions": [
            {
                "merchant": t.merchant,
                "amount": t.amount,
                "type": t.transaction_type,
                "category": t.category,
                "date": str(t.transaction_date),
            }
            for t in transactions
        ]
    }

    answer = ask_financial_copilot(question, financial_context)

    return {
        "user_id": user_id,
        "question": question,
        "answer": answer
    }