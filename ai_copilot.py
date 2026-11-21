import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def ask_financial_copilot(question: str, financial_context: dict) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Groq API key is not configured."

    try:
        client = Groq(api_key=api_key)

        prompt = f"""
You are an intelligent personal finance coach.

Act as a professional financial advisor who is friendly,
practical, honest, and easy to understand.

Analyze the user's actual financial data.
Never invent financial numbers.

FINANCIAL CONTEXT:
{financial_context}

USER QUESTION:
{question}

INSTRUCTIONS:
- Give a clear and direct answer.
- Use actual financial information provided.
- Explain financial concepts simply.
- Identify risks and overspending.
- Suggest realistic ways to save money.
- Consider the user's financial goals.
- Use Indian Rupees (₹).
- Avoid generic advice.
- Never guarantee investment returns.
- Use headings and bullet points where appropriate.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert personal finance coach specializing in Indian personal finance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content

        if answer:
            return answer

        return "Groq returned an empty response."

    except Exception as e:
        return f"Groq AI error: {str(e)}"