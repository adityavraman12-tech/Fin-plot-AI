def categorize_transaction(merchant: str, description: str = "") -> str:

    text = f"{merchant} {description}".lower()

    rules = {
        "Food & Dining": [
            "swiggy", "zomato", "restaurant",
            "cafe", "pizza", "food"
        ],
        "Transportation": [
            "uber", "ola", "metro", "fuel",
            "petrol", "rapido"
        ],
        "Shopping": [
            "amazon", "flipkart", "myntra",
            "shopping"
        ],
        "Bills & Utilities": [
            "electricity", "water bill",
            "recharge", "airtel", "jio"
        ],
        "Entertainment": [
            "netflix", "spotify", "movie",
            "gaming"
        ],
        "Healthcare": [
            "hospital", "pharmacy",
            "medical", "doctor"
        ],
    }

    for category, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Uncategorized"