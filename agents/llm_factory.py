import os
from pathlib import Path
from dotenv import load_dotenv

# Φόρτωση .env από root του project (ένα επίπεδο πάνω από agents/)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


def get_llm(temperature: float = 0):
    """
    Επιστρέφει το LLM instance.
    Προτεραιότητα: OpenAI → Gemini → Error
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if openai_key:
        # ── OpenAI provider (gpt-4.1 για hackathon) ──────────────
        from langchain_openai import ChatOpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=openai_key,
        )

    elif google_key:
        # ── Gemini fallback ───────────────────────────────────────
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=google_key,
        )

    else:
        raise ValueError(
            "CRITICAL: Δεν βρέθηκε κανένα API key. "
            "Πρόσθεσε OPENAI_API_KEY ή GOOGLE_API_KEY στο .env"
        )