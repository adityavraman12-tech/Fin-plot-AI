
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.categorizer import categorize_transaction
from app.services.statement_parser import parse_statement
from app.services.merchant_normalizer import normalize_merchant


router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"]
)


# =========================================================
# CREATE SINGLE TRANSACTION
# =========================================================

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    category = transaction.category

    if not category:
        category = categorize_transaction(
            transaction.merchant,
            transaction.description or ""
        )

    new_transaction = Transaction(
        user_id=transaction.user_id,
        merchant=normalize_merchant(transaction.merchant),
        description=transaction.description,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        category=category,
        transaction_date=transaction.transaction_date,
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


# =========================================================
# UPLOAD BANK STATEMENT (CSV)
# =========================================================

@router.post("/upload")
async def upload_statement(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file."
        )

    try:
        transactions = parse_statement(file.file)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse statement: {str(e)}"
        )

    imported = 0
    duplicates = 0

    try:
        for transaction in transactions:

            original_description = transaction["description"]

            merchant = normalize_merchant(
                transaction["merchant"]
            )

            amount = transaction["amount"]
            transaction_date = transaction["transaction_date"]
            transaction_type = transaction["transaction_type"]

            category = categorize_transaction(
                merchant,
                original_description
            )

            # Check for duplicates using amount, date,
            # transaction type, and normalized merchant.
            existing_transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.amount == amount,
                Transaction.transaction_date == transaction_date,
                Transaction.transaction_type == transaction_type
            ).all()

            duplicate_found = any(
                normalize_merchant(existing.merchant) == merchant
                for existing in existing_transactions
            )

            if duplicate_found:
                duplicates += 1
                continue

            new_transaction = Transaction(
                user_id=user_id,
                merchant=merchant,
                description=original_description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                transaction_date=transaction_date,
            )

            db.add(new_transaction)
            imported += 1

        db.commit()

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

    return {
        "message": "Statement processed successfully",
        "filename": file.filename,
        "total_transactions_found": len(transactions),
        "imported": imported,
        "duplicates_skipped": duplicates
    }


# =========================================================
# GET FINANCIAL SUMMARY
# IMPORTANT: MUST BE ABOVE /{transaction_id}
# =========================================================

@router.get("/summary")
def get_financial_summary(
    user_id: str,
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

    total_income = sum(
        float(t.amount)
        for t in transactions
        if t.transaction_type == "income"
    )

    total_expenses = sum(
        float(t.amount)
        for t in transactions
        if t.transaction_type == "expense"
    )

    category_breakdown = {}

    for transaction in transactions:

        if transaction.transaction_type != "expense":
            continue

        category = transaction.category or "Uncategorized"

        category_breakdown[category] = (
            category_breakdown.get(category, 0)
            + float(transaction.amount)
        )

    return {
        "user_id": user_id,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_cash_flow": round(
            total_income - total_expenses, 2
        ),
        "transaction_count": len(transactions),
        "spending_by_category": {
            category: round(amount, 2)
            for category, amount in category_breakdown.items()
        }
    }


# =========================================================
# GET ALL TRANSACTIONS
# =========================================================

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    user_id: str,
    db: Session = Depends(get_db)
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )


# =========================================================
# GET SINGLE TRANSACTION
# Keep this LAST because it matches dynamic paths.
# =========================================================

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction
