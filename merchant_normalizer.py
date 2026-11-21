import re


def normalize_merchant(name: str) -> str:
    if not name:
        return "Unknown"

    text = name.strip().lower()

    # Specific merchants first
    if "swiggy instamart" in text or "instamart" in text:
        return "Swiggy Instamart"

    if "swiggy" in text:
        return "Swiggy"

    if "zomato" in text:
        return "Zomato"

    if "dmart" in text or "d mart" in text:
        return "DMart"

    if "amazon" in text:
        return "Amazon"

    if "flipkart" in text:
        return "Flipkart"

    if "uber" in text:
        return "Uber"

    if "ola" in text:
        return "Ola"

    if "netflix" in text:
        return "Netflix"

    if "spotify" in text:
        return "Spotify"

    if "jio" in text:
        return "Jio"

    if "airtel" in text:
        return "Airtel"

    # Remove common banking prefixes
    text = re.sub(
        r"\b(upi|pos|imps|neft|rtgs|txn|transaction)\b",
        "",
        text
    )

    # Remove generic transaction words
    text = re.sub(
        r"\b(payment|purchase|order|food|bill|transfer)\b",
        "",
        text
    )

    # Remove special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "Unknown"

    return text.title()