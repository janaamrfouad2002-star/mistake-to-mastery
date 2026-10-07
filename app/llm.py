"""llm.py - the AI layer. It only writes explanations; it never grades."""
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core import template_explain

load_dotenv()                      # reads GOOGLE_API_KEY from the .env file
MODEL = "gemini-2.5-flash"         # check AI Studio for the current free model name

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a kind maths tutor. The error below was verified by software, "
     "so do not question it and never solve the whole problem. "
     "Reply in under 80 words: explain the misconception simply, then ask ONE "
     "short question that helps the student notice the mistake. "
     "If the error type is UNKNOWN, say your guess is unverified."),
    ("human",
     "The student went from:\n{prev}\nto:\n{wrong}\nVerified error type: {tag}"),
])


def _get_model():
    """Swap providers here: Groq or Ollama are one-line changes."""
    if not os.getenv("GOOGLE_API_KEY"):
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=MODEL, temperature=0.3)


def explain_with_llm(prev: str, wrong: str, tag: str) -> str:
    model = _get_model()
    if model is not None:
        try:
            chain = PROMPT | model | StrOutputParser()
            return chain.invoke({"prev": prev, "wrong": wrong, "tag": tag})
        except Exception:
            pass                   # network, quota, or key problem: fall back
    text, question = template_explain(tag)
    return f"{text}\n\n**Think about it:** {question}"