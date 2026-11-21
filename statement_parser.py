import pandas as pd
from datetime import datetime


def parse_statement(file):
    df = pd.read_csv(file)

    # Normalize column names
    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    # Find date column
    date_col = next(
        (c for c in df.columns if "date" in c),
        None
    )

    # Find description column
    description_col = next(
        (c for c in df.columns
         if any(x in c for x in ["description", "narration", "merchant", "particular"])),
        None
    )

    # Find amount column
    amount_col = next(
        (c for c in df.columns
         if c in ["amount", "transaction_amount", "amt"]),
        None
    )

    debit_col = next(
        (c for c in df.columns
         if any(x in c for x in ["debit", "withdrawal"])),
        None
    )

    credit_col = next(
        (c for c in df.columns
         if any(x in c for x in ["credit", "deposit"])),
        None
    )

    if not date_col or not description_col:
        raise ValueError(
            "Could not identify date and description columns."
        )

    if not amount_col and not debit_col and not credit_col:
        raise ValueError(
            "Could not identify transaction amount columns."
        )

    transactions = []

    for _, row in df.iterrows():

        date = pd.to_datetime(
            row[date_col],
            errors="coerce",
            dayfirst=True
        )

        if pd.isna(date):
            continue

        description = str(row[description_col]).strip()

        if not description or description.lower() == "nan":
            continue

        # Handle separate debit and credit columns
        if debit_col and credit_col:

            debit = pd.to_numeric(
                row[debit_col], errors="coerce"
            )

            credit = pd.to_numeric(
                row[credit_col], errors="coerce"
            )

            debit = 0 if pd.isna(debit) else abs(debit)
            credit = 0 if pd.isna(credit) else abs(credit)

            if debit > 0:
                amount = debit
                transaction_type = "expense"

            elif credit > 0:
                amount = credit
                transaction_type = "income"

            else:
                continue

        else:

            amount = pd.to_numeric(
                row[amount_col], errors="coerce"
            )

            if pd.isna(amount) or amount == 0:
                continue

            transaction_type = (
                "income" if amount > 0 else "expense"
            )

            amount = abs(amount)

        transactions.append({
            "merchant": description[:255],
            "description": description,
            "amount": float(amount),
            "transaction_type": transaction_type,
            "transaction_date": date.date()
        })

    return transactions