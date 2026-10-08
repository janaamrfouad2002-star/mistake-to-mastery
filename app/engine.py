"""engine.py - sends a structured problem to the right verifier module."""
from typing import Literal

from pydantic import BaseModel, Field
from sympy import integrate, solve as sym_solve

from app import calculus, core

core.EXPLANATIONS.update(calculus.EXPLANATIONS)


class Extracted(BaseModel):
    """What the LLM extracts from the student's text and/or photo."""
    subject: Literal["algebra", "derivative", "integral", "other"] = "other"
    steps: list[str] = Field(default_factory=list)   # algebra: every equation in order
    expression: str = ""                             # calculus: the function
    student_answer: str = ""                         # calculus: the student's answer, if any


def solve_question(ex: Extracted) -> dict:
    """No attempt given: SymPy computes the correct answer."""
    if ex.subject == "derivative" and ex.expression.strip():
        f = calculus.parse(ex.expression)
        return {"status": "solved", "subject": "derivative",
                "question": f"derivative of {ex.expression}", "answer": str(f.diff(core.x))}
    if ex.subject == "integral" and ex.expression.strip():
        f = calculus.parse(ex.expression)
        return {"status": "solved", "subject": "integral",
                "question": f"integral of {ex.expression}", "answer": f"{integrate(f, core.x)} + C"}
    if ex.subject == "algebra" and ex.steps:
        eq = core.parse_equation(ex.steps[0].replace("^", "**"))
        return {"status": "solved", "subject": "algebra",
                "question": ex.steps[0], "answer": f"x = {sym_solve(eq, core.x)}"}
    return {"status": "unsupported"}


def analyse(ex: Extracted) -> dict:
    if ex.subject == "algebra":
        if len(ex.steps) >= 2:
            steps = [s.replace("^", "**") for s in ex.steps]
            i = core.first_wrong_step(steps)
            if i is None:
                return {"status": "correct", "subject": "algebra"}
            return {"status": "wrong", "subject": "algebra",
                    "tag": core.diagnose(steps[i - 1], steps[i]),
                    "prev": steps[i - 1], "wrong": steps[i]}
        return solve_question(ex)
    if ex.subject in ("derivative", "integral"):
        if ex.student_answer.strip():
            return calculus.check(ex.subject, ex.expression, ex.student_answer)
        return solve_question(ex)
    return {"status": "unsupported"}


def make_twin(subject: str, tag: str) -> str:
    if subject == "algebra":
        return core.make_problem(tag)
    return calculus.make_problem(subject, tag)


def check_twin(subject: str, problem: str, student_text: str) -> bool:
    if subject == "algebra":
        steps = [problem] + [s.strip().replace("^", "**")
                             for s in student_text.splitlines() if s.strip()]
        return len(steps) > 1 and core.first_wrong_step(steps) is None
    return calculus.check(subject, problem, student_text)["status"] == "correct"