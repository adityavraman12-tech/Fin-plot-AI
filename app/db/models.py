from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    Boolean,
    DateTime,
)
from sqlalchemy.sql import func

from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    merchant = Column(String, nullable=False)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    transaction_date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)

    monthly_income = Column(Float, default=0)
    monthly_fixed_expenses = Column(Float, default=0)
    current_savings = Column(Float, default=0)
    emergency_fund = Column(Float, default=0)

    financial_goal = Column(String, nullable=True)
    goal_amount = Column(Float, default=0)
    goal_deadline = Column(Date, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )