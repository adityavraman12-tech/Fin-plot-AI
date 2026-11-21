import os
from groq import Groq


def ask_financial_copilot(question: str, financial_context: dict) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "AI service is not configured. Please add your Groq API key."

    client = Groq(api_key=api_key)

    system_prompt = """
    You are Fin-Plot AI, an intelligent personal financial coach.

    Your role:
    - Analyze the user's actual financial data.
    - Give practical, personalized financial advice.
    - Identify overspending and unnecessary expenses.
    - Help users budget, save money, and achieve financial goals.
    - Explain financial concepts in simple language.
    - Be honest, realistic, and supportive.
    - Never invent financial data.
    - If information is missing, clearly mention it.
    - Avoid generic advice when actual data is available.

    Format responses clearly using headings and bullet points when useful.
    Use Indian Rupees (₹) when the user's data is in INR.
    """

    user_prompt = f"""
    USER FINANCIAL DATA:
    {financial_context}

    USER QUESTION:
    {question}

    Analyze the available data and provide a personalized response.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI analysis failed: {str(e)}"