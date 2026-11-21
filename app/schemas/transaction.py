from datetime import date
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    user_id: str
    merchant: str
    description: str | None = None
    amount: float = Field(gt=0)
    transaction_type: str
    transaction_date: date
    category: str | None = None


class TransactionResponse(TransactionCreate):
    id: int
    is_recurring: bool

    class Config:
        from_attributes = True