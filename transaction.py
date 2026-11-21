from datetime import date

from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    merchant: str
    description: str | None = None
    amount: float = Field(gt=0)
    transaction_type: str
    transaction_date: date
    category: str | None = None


class TransactionResponse(TransactionCreate):
    id: int
    user_id: str
    is_recurring: bool

    model_config = ConfigDict(from_attributes=True)