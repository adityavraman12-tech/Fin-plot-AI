from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict


class FinancialProfileCreate(BaseModel):
    monthly_income: float = Field(default=0, ge=0)
    monthly_fixed_expenses: float = Field(default=0, ge=0)
    current_savings: float = Field(default=0, ge=0)
    emergency_fund: float = Field(default=0, ge=0)

    financial_goal: str | None = None
    goal_amount: float = Field(default=0, ge=0)
    goal_deadline: date | None = None


class FinancialProfileResponse(FinancialProfileCreate):
    id: int
    user_id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)