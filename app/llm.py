"""llm.py - the AI layer. It only reads, explains and answers; it never grades."""
import base64
import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core import template_explain
from app.engine import Extracted

load_dotenv()
MODEL = "gemini-3.5-flash-lite"    # Gemini model, used for photos. Change here if retired.

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a kind maths tutor. The error below was verified by software, "
     "so do not question it and never solve the whole problem. "
     "Reply in under 80 words: explain the misconception simply, then ask ONE "
     "short question that helps the student notice the mistake. "
     "If the error type is UNKNOWN, say your guess is unverified. "
     "Reply in {lang}."),
    ("human",
     "The student went from:\n{prev}\nto:\n{wrong}\nVerified error type: {tag}"),
])


def _get_model(vision: bool = False):
    """Pick the provider with LLM_PROVIDER in .env: groq, gemini or ollama.
    vision=True forces Gemini, because the Groq text models can't read photos."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    if vision:
        provider = "gemini"
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"), temperature=0.3)
    if provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            return None
        from langchain_groq import ChatGroq
        return ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                        temperature=0.3, timeout=30, max_retries=1)
    if not os.getenv("GOOGLE_API_KEY"):
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=MODEL, temperature=0.3, timeout=60, max_retries=2)


def _text(resp) -> str:
    """Models may return a string or a list of parts. Always give back plain text."""
    c = resp.content
    if isinstance(c, str):
        return c
    return "".join(p if isinstance(p, str) else p.get("text", "") for p in c)


_TR_CACHE = {}


def translate_text(text: str, lang: str) -> str:
    """Translate fixed texts (template hints, mistake names). Falls back to the original."""
    if not text or lang == "English":
        return text
    key = (text, lang)
    if key in _TR_CACHE:
        return _TR_CACHE[key]
    model = _get_model()
    if model is None:
        return text
    try:
        msgs = [SystemMessage(content=(
                    f"Translate into {lang}. Keep maths symbols, numbers and text in backticks "
                    "unchanged. Reply with the translation only.")),
                HumanMessage(content=text)]
        out = _text(model.invoke(msgs)).strip()
        if out:
            _TR_CACHE[key] = out
            return out
    except Exception as e:
        print("LLM ERROR:", e)
    return text


def explain_with_llm(prev: str, wrong: str, tag: str, lang: str = "English") -> str:
    model = _get_model()
    if model is not None:
        try:
            chain = PROMPT | model | StrOutputParser()
            return chain.invoke({"prev": prev, "wrong": wrong, "tag": tag, "lang": lang})
        except Exception as e:
            print("LLM ERROR:", e)
    text, question = template_explain(tag)
    return translate_text(f"{text}\n\n**Think about it:** {question}", lang)


EXTRACT_SYSTEM = (
    "You convert a student's message and/or photo into structured data. "
    "The student may write or speak in English, Hindi, Arabic or French. "
    "NEVER solve, fix or improve anything: copy exactly what the student wrote, "
    "including their mistakes. If handwriting is unclear, give your best reading. "
    "If maths is spoken in words (like 'x squared plus three x'), write it as symbols (x^2 + 3x). "
    "subject is 'algebra' for equations to solve: put every equation in steps, in order "
    "(a single equation with no working is fine). "
    "subject is 'derivative' or 'integral' for differentiating or integrating: put the "
    "function in expression, and the student's final answer in student_answer (empty if none). "
    "subject is 'chemistry_balance' for balancing a chemical equation: put the unbalanced "
    "equation in expression using -> (like H2 + O2 -> H2O), and the student's balanced attempt, "
    "if any, in student_answer. "
    "subject is 'physics_calc' for a numeric physics or unit calculation: put the calculation in "
    "expression with units and brackets around every denominator (like 20 m / (4 s)), and the "
    "student's answer with units in student_answer (empty if none). "
    "Anything else (biology, history, languages, theory questions) is 'other'. "
    "Always write maths in plain ASCII with digits 0-9, like 2x + 3 = 11, x^2, sin(x)."
)


def _content(text: str, image_bytes, mime: str):
    parts = [{"type": "text", "text": text or "Read the student's work in the image."}]
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts


def _offline_extract(text: str) -> Extracted:
    """No AI needed: simple pattern matching for the easy cases (English only)."""
    low = text.lower().strip()
    m = re.search(r"(derivative|differentiate|integral|integrate)\s*(?:of)?\s*(.+)", low)
    if m:
        kind = "derivative" if m.group(1) in ("derivative", "differentiate") else "integral"
        return Extracted(subject=kind, expression=m.group(2).strip(" ?."))
    steps = [s.strip() for s in text.splitlines() if "=" in s]
    if steps:
        return Extracted(subject="algebra", steps=steps)
    return Extracted(subject="other")


def extract(text: str, image_bytes=None, mime: str = "image/png") -> Extracted:
    model = _get_model(vision=bool(image_bytes))
    if model is not None:
        try:
            msgs = [SystemMessage(content=EXTRACT_SYSTEM),
                    HumanMessage(content=_content(text, image_bytes, mime))]
            return model.with_structured_output(Extracted).invoke(msgs)
        except Exception as e:
            print("LLM ERROR:", e)
    return _offline_extract(text)


def explain_solution(question: str, answer: str, lang: str = "English", label: str = None) -> str:
    """Software already computed the answer; the AI only explains how to get there."""
    base = f"**{label or 'Answer (computed by software)'}:** `{answer}`"
    model = _get_model()
    if model is None:
        return base
    try:
        msgs = [SystemMessage(content=(
                    "A tutor for school students. Software computed the correct answer. "
                    "Never change it. Explain the method in simple words, in at most 6 short "
                    f"steps. Reply in {lang}.")),
                HumanMessage(content=f"Question: {question}\nCorrect answer: {answer}")]
        return base + "\n\n" + _text(model.invoke(msgs))
    except Exception as e:
        print("LLM ERROR:", e)
        return base


def answer_question(text: str, image_bytes=None, mime: str = "image/png",
                    lang: str = "English") -> str:
    """For subjects with no verifier. Not checked by software."""
    model = _get_model(vision=bool(image_bytes))
    if model is None:
        return "I need an AI key in `.env` to answer this kind of question."
    try:
        msgs = [SystemMessage(content=(
                    "You are a kind tutor for school students in any subject (maths, physics, "
                    "chemistry, biology, languages and more). Answer in simple language, step by "
                    "step, and keep it short. If the student included their own attempt, point out "
                    "exactly where it goes wrong. If you are not sure, say so. "
                    f"Always reply in {lang}.")),
                HumanMessage(content=_content(text, image_bytes, mime))]
        return _text(model.invoke(msgs))
    except Exception as e:
        print("LLM ERROR:", e)
        return "Sorry, I couldn't reach the AI just now. Please try again."


def simplify(text: str, lang: str = "English"):
    """Used by the thumbs-down gesture: explain the last answer again, more simply."""
    model = _get_model()
    if model is None:
        return None
    try:
        msgs = [SystemMessage(content=(
                    "You are a kind tutor for school students. The student did not understand "
                    "the explanation below. Explain it again more simply, with one small example, "
                    f"in at most 5 short sentences. Reply in {lang}.")),
                HumanMessage(content=text)]
        return _text(model.invoke(msgs))
    except Exception as e:
        print("LLM ERROR:", e)
        return None