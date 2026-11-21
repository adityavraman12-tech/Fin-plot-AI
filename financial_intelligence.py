from datetime import date
from app.db.models import Transaction, FinancialProfile


def generate_financial_insights(db, user_id: str):

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == user_id
    ).first()

    if not profile:
        return {"error": "Financial profile not found"}

    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

    income = profile.monthly_income
    fixed_expenses = profile.monthly_fixed_expenses
    savings = profile.current_savings
    emergency_fund = profile.emergency_fund

    monthly_surplus = income - fixed_expenses

    savings_rate = (
        (monthly_surplus / income) * 100
        if income > 0 else 0
    )

    emergency_coverage = (
        emergency_fund / fixed_expenses
        if fixed_expenses > 0 else 0
    )

    emergency_target = fixed_expenses * 3

    emergency_shortfall = max(
        emergency_target - emergency_fund,
        0
    )

    goal_amount = profile.goal_amount

    goal_remaining = max(
        goal_amount - savings,
        0
    )

    months_remaining = None
    monthly_goal_saving = None
    goal_feasible = None

    if profile.goal_deadline:

        today = date.today()

        deadline = profile.goal_deadline

        months_remaining = max(
            (deadline.year - today.year) * 12
            + deadline.month - today.month,
            0
        )

        if months_remaining > 0:

            monthly_goal_saving = (
                goal_remaining / months_remaining
            )

            goal_feasible = (
                monthly_goal_saving <= monthly_surplus
            )

        else:

            monthly_goal_saving = goal_remaining

            goal_feasible = (
                goal_remaining <= monthly_surplus
            )

    total_income = sum(
        t.amount for t in transactions
        if t.transaction_type == "income"
    )

    total_expenses = sum(
        t.amount for t in transactions
        if t.transaction_type == "expense"
    )

    transaction_surplus = total_income - total_expenses

    category_spending = {}

    for t in transactions:

        if t.transaction_type == "expense":

            category = t.category or "Uncategorized"

            category_spending[category] = (
                category_spending.get(category, 0)
                + t.amount
            )

    insights = []

    if savings_rate >= 20:
        insights.append(
            "Your profile-based savings rate is healthy."
        )
    else:
        insights.append(
            "Your savings rate is below 20%. "
            "Review expenses to increase savings."
        )

    if emergency_coverage < 1:
        insights.append(
            "Your emergency fund covers less than "
            "one month of fixed expenses."
        )

    if emergency_shortfall > 0:
        insights.append(
            f"You need ₹{emergency_shortfall:.2f} more "
            "to reach a 3-month emergency fund."
        )

    if goal_feasible is not None:

        if goal_feasible:
            insights.append(
                "Your financial goal appears achievable "
                "within your estimated monthly surplus."
            )
        else:
            insights.append(
                "Your financial goal requires more monthly "
                "savings than your estimated surplus."
            )

    return {
        "user_id": user_id,

        "financial_health": {
            "monthly_income": income,
            "monthly_fixed_expenses": fixed_expenses,
            "monthly_surplus": monthly_surplus,
            "savings_rate_percent": round(savings_rate, 2),
        },

        "emergency_fund": {
            "current_amount": emergency_fund,
            "months_of_coverage": round(
                emergency_coverage, 2
            ),
            "three_month_target": emergency_target,
            "shortfall": emergency_shortfall,
        },

        "financial_goal": {
            "goal": profile.financial_goal,
            "target_amount": goal_amount,
            "current_savings": savings,
            "estimated_remaining": goal_remaining,
            "deadline": profile.goal_deadline,
            "months_remaining": months_remaining,
            "required_monthly_saving": (
                round(monthly_goal_saving, 2)
                if monthly_goal_saving is not None
                else None
            ),
            "achievable": goal_feasible,
        },

        "transaction_analysis": {
            "transaction_income": total_income,
            "transaction_expenses": total_expenses,
            "transaction_surplus": transaction_surplus,
            "transaction_count": len(transactions),
            "category_spending": category_spending,
        },

        "insights": insights,
    }