"""core.py - the deterministic engine. No AI in this file."""
import random
import sqlite3
import time

from sympy import Eq, symbols, solve, simplify
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)

x = symbols("x")
T = standard_transformations + (implicit_multiplication_application,)

# ---------- 1. CHECKER: find the first wrong line ----------

def parse_equation(s: str) -> Eq:
    left, right = s.split("=")
    return Eq(parse_expr(left, transformations=T), parse_expr(right, transformations=T))


def parse_equation_raw(s: str) -> Eq:
    """Parse WITHOUT auto-simplifying, so 3(x+4) stays as 3(x+4)."""
    left, right = s.split("=")
    return Eq(
        parse_expr(left, transformations=T, evaluate=False),
        parse_expr(right, transformations=T, evaluate=False),
        evaluate=False,
    )


def equivalent(a: str, b: str) -> bool:
    return set(solve(parse_equation(a), x)) == set(solve(parse_equation(b), x))


def first_wrong_step(steps: list[str]):
    """Index of the first incorrect step (>=1), or None if all valid."""
    for i in range(1, len(steps)):
        if not equivalent(steps[i - 1], steps[i]):
            return i
    return None

# ---------- 2. BUG LIBRARY: name the misconception ----------

def _linear_parts(L):
    b, dep = L.as_independent(x, as_Add=True)
    a = dep.coeff(x)
    if a == 0:
        return None
    return a, b


def sign_error(L, R):
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(a * x, R + b)


def forgot_to_divide(L, R):
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(x, R - b)


def multiplied_instead_of_divided(L, R):
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(x, (R - b) * a)


def forgot_to_distribute(L, R):
    k, rest = L.as_independent(x)
    if rest.is_Add and k != 1:
        ind, dep = rest.as_independent(x, as_Add=True)
        return Eq(k * dep + ind, R)


BUGS = {
    "SIGN_ERROR_MOVING_TERM": sign_error,
    "FORGOT_TO_DIVIDE": forgot_to_divide,
    "MULTIPLIED_INSTEAD_OF_DIVIDED": multiplied_instead_of_divided,
    "FORGOT_TO_DISTRIBUTE": forgot_to_distribute,
}


def _same(e1: Eq, e2: Eq) -> bool:
    return simplify(e1.lhs - e2.lhs) == 0 and simplify(e1.rhs - e2.rhs) == 0


def diagnose(prev_step: str, wrong_step: str) -> str:
    prevs = [parse_equation(prev_step), parse_equation_raw(prev_step)]
    stu = parse_equation(wrong_step)
    for tag, fn in BUGS.items():
        for prev in prevs:
            try:
                cand = fn(prev.lhs, prev.rhs)
            except Exception:
                cand = None
            if cand is not None and _same(cand, stu):
                return tag
    return "UNKNOWN"

# ---------- 3. TWIN PROBLEMS ----------

def make_problem(tag: str) -> str:
    x0 = random.randint(-9, 9)
    a = random.choice([2, 3, 4, 5, 6])
    b = random.randint(2, 9)
    if tag == "FORGOT_TO_DISTRIBUTE":
        return f"{a}(x + {b}) = {a * (x0 + b)}"
    return f"{a}x + {b} = {a * x0 + b}"

# ---------- 4. TEMPLATE EXPLANATIONS (used when no AI is available) ----------

EXPLANATIONS = {
    "SIGN_ERROR_MOVING_TERM": (
        "When you move a number across the equals sign, you do the opposite operation. "
        "Adding 3 on one side becomes subtracting 3 on the other.",
        "What happens if you subtract the same number from both sides?"),
    "FORGOT_TO_DIVIDE": (
        "After isolating the x-term, x is still multiplied by a number. You need one more step.",
        "What is x multiplied by, and how do you undo multiplication?"),
    "MULTIPLIED_INSTEAD_OF_DIVIDED": (
        "To undo multiplication you divide, not multiply.",
        "If 2x = 8, what number times 2 gives 8?"),
    "FORGOT_TO_DISTRIBUTE": (
        "A number outside brackets multiplies everything inside, not just the first term.",
        "In 3(x + 4), what is 3 times each of the two terms?"),
    "UNKNOWN": (
        "This step changes the answer, but it doesn't match a mistake I know yet.",
        "Can you check this line by substituting your answer back in?"),
}


def template_explain(tag: str):
    return EXPLANATIONS.get(tag, EXPLANATIONS["UNKNOWN"])

# ---------- 5. LEARNER MEMORY (SQLite) ----------

DB = "learner.db"
INTERVALS = [0, 1, 3, 7, 14]   # days until review, by box number


def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS mistakes(
        user TEXT, tag TEXT, errors INT DEFAULT 0, box INT DEFAULT 0,
        next_review REAL, PRIMARY KEY(user, tag))""")
    return c


def record(user: str, tag: str, correct: bool):
    c = conn()
    c.execute("INSERT OR IGNORE INTO mistakes(user, tag, next_review) VALUES(?,?,?)",
              (user, tag, time.time()))
    row = c.execute("SELECT box FROM mistakes WHERE user=? AND tag=?", (user, tag)).fetchone()
    box = min(row[0] + 1, len(INTERVALS) - 1) if correct else 0
    nxt = time.time() + INTERVALS[box] * 86400
    c.execute("""UPDATE mistakes SET box=?, next_review=?, errors=errors+?
                 WHERE user=? AND tag=?""", (box, nxt, 0 if correct else 1, user, tag))
    c.commit()
    c.close()


def due(user: str):
    c = conn()
    rows = [r[0] for r in c.execute(
        "SELECT tag FROM mistakes WHERE user=? AND next_review<=?", (user, time.time()))]
    c.close()
    return rows


def mistake_map(user: str):
    c = conn()
    rows = c.execute(
        "SELECT tag, errors, box FROM mistakes WHERE user=? ORDER BY errors DESC", (user,)).fetchall()
    c.close()
    return rows