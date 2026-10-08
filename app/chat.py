"""chat.py - one function that every front end (web, Telegram, WhatsApp) calls."""
from app.core import record
from app.engine import analyse, make_twin, check_twin
from app.llm import extract, explain_with_llm, explain_solution, answer_question

PENDING = {}   # user id -> the twin problem they were last given (in memory only)


def handle(user: str, text: str, image=None, mime: str = "image/png") -> str:
    text = text or ""

    # The student is answering a practice problem: "answer: ..."
    if text.lower().startswith("answer:") and user in PENDING:
        tw = PENDING.pop(user)
        try:
            ok = check_twin(tw["subject"], tw["problem"], text[7:].strip())
        except Exception:
            return "I couldn't read your answer. Try again with `answer: ...`"
        record(user, tw["tag"], correct=ok)
        return "Fixed it! ✅" if ok else "Same trouble, we'll review this again later."

    ex = extract(text, image, mime)
    try:
        result = analyse(ex)
    except Exception:
        return "I couldn't read the maths. If I misread your photo, please type the problem."

    status = result["status"]
    if status == "correct":
        return "All correct! ✅"
    if status == "solved":
        return explain_solution(result["question"], result["answer"])
    if status == "unsupported":
        return answer_question(text, image, mime) + "\n\n(Not verified by software.)"

    hint = explain_with_llm(result["prev"], result["wrong"], result["tag"])
    record(user, result["tag"], correct=False)
    twin = make_twin(result["subject"], result["tag"])
    PENDING[user] = {"subject": result["subject"], "tag": result["tag"], "problem": twin}
    return (f"Verified mistake: {result['tag']}\n\nYour line: {result['wrong']}\n\n{hint}\n\n"
            f"Try a similar one: {twin}\nReply with: answer: your working")