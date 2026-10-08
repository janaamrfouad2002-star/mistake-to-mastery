"""llm.py - the AI layer. It only writes explanations; it never grades."""
import base64
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core import template_explain
from app.engine import Extracted

load_dotenv()                      # reads GOOGLE_API_KEY from the .env file
MODEL = "gemini-3.8-flash"         # one place to change if Google retires the name

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
    return ChatGoogleGenerativeAI(model=MODEL, temperature=0.3, timeout=30, max_retries=1)


def _text(resp) -> str:
    """Gemini may return a string or a list of parts. Always give back plain text."""
    c = resp.content
    if isinstance(c, str):
        return c
    return "".join(p if isinstance(p, str) else p.get("text", "") for p in c)


def explain_with_llm(prev: str, wrong: str, tag: str) -> str:
    model = _get_model()
    if model is not None:
        try:
            chain = PROMPT | model | StrOutputParser()
            return chain.invoke({"prev": prev, "wrong": wrong, "tag": tag})
        except Exception as e:
            print("GEMINI ERROR:", e)    # network, quota, or key problem: fall back
    text, question = template_explain(tag)
    return f"{text}\n\n**Think about it:** {question}"


EXTRACT_SYSTEM = (
    "You convert a student's message and/or photo into structured data. "
    "NEVER solve, fix or improve anything: copy exactly what the student wrote, "
    "including their mistakes. If handwriting is unclear, give your best reading. "
    "subject is 'algebra' for equations to solve: put every equation in steps, in order "
    "(a single equation with no working is fine). "
    "subject is 'derivative' or 'integral' for differentiating or integrating: put the "
    "function in expression, and the student's final answer in student_answer, or leave "
    "student_answer empty if the student gave no answer. "
    "Anything else (physics, chemistry, differential equations, languages) is 'other'. "
    "Write maths as plain text, like 2x + 3 = 11, x^2, sin(x)."
)


def _content(text: str, image_bytes, mime: str):
    parts = [{"type": "text", "text": text or "Read the student's work in the image."}]
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts


def extract(text: str, image_bytes=None, mime: str = "image/png") -> Extracted:
    model = _get_model()
    if model is not None:
        try:
            msgs = [SystemMessage(content=EXTRACT_SYSTEM),
                    HumanMessage(content=_content(text, image_bytes, mime))]
            return model.with_structured_output(Extracted).invoke(msgs)
        except Exception as e:
            print("GEMINI ERROR:", e)
    # Offline fallback: lines containing "=" are algebra steps
    steps = [s.strip() for s in text.splitlines() if "=" in s]
    if steps:
        return Extracted(subject="algebra", steps=steps)
    return Extracted(subject="other")


def explain_solution(question: str, answer: str) -> str:
    """SymPy already computed the answer; Gemini only explains how to get there."""
    model = _get_model()
    if model is None:
        return f"**Answer (computed by SymPy):** `{answer}`"
    try:
        msgs = [SystemMessage(content=(
                    "A maths tutor. Software computed the correct answer. Never change it. "
                    "Explain the method in simple words, in at most 6 short steps.")),
                HumanMessage(content=f"Question: {question}\nCorrect answer: {answer}")]
        return f"**Answer (computed by SymPy):** `{answer}`\n\n" + _text(model.invoke(msgs))
    except Exception as e:
        print("GEMINI ERROR:", e)
        return f"**Answer (computed by SymPy):** `{answer}`"


def answer_question(text: str, image_bytes=None, mime: str = "image/png") -> str:
    """For subjects with no verifier yet. Not checked by software."""
    model = _get_model()
    if model is None:
        return "I need a Gemini key in `.env` to answer this kind of question."
    try:
        msgs = [SystemMessage(content=(
                    "You are a kind tutor for students. Answer in simple language, step by step. "
                    "If the student included their own attempt, point out where it goes wrong.")),
                HumanMessage(content=_content(text, image_bytes, mime))]
        return _text(model.invoke(msgs))
    except Exception as e:
        print("GEMINI ERROR:", e)
        return "Sorry, I couldn't reach the AI just now. Please try again."