"""calculus.py - verifier module for derivatives and integrals (no AI)."""
import random
import re

from sympy import Dummy, integrate, simplify
from sympy.parsing.sympy_parser import parse_expr

from app.core import T, x


def clean(s: str) -> str:
    """Fix photo symbols, add brackets to 'cos x', remove 'dy/dx =' prefixes."""
    s = s.strip()
    for a, b in {"−": "-", "–": "-", "×": "*", "·": "*", "÷": "/",
                 "²": "^2", "³": "^3", "$": "", "\\": ""}.items():
        s = s.replace(a, b)
    s = re.sub(r"\b(sin|cos|tan|ln|exp)\s+([a-z0-9]+)", r"\1(\2)", s)
    s = re.sub(r"^\s*(dy\s*/\s*dx|d\s*/\s*dx|f\s*'\s*\(x\)|y\s*')\s*=", "", s)
    if "=" in s:
        s = s.split("=")[-1]
    return s.strip()


def parse(s: str):
    return parse_expr(clean(s).replace("^", "**"), transformations=T)


def _coef_power(f):
    """Reads c*x**n. Returns (c, n) or None."""
    c, r = f.as_independent(x, as_Add=False)
    if r == x:
        return c, 1
    if r.is_Pow and r.base == x and r.exp.is_number:
        return c, r.exp
    return None


# ---------- derivative bugs: each returns the WRONG answer a student might give ----------

def d_power_not_reduced(f):          # x^3 -> 3x^3
    p = _coef_power(f)
    if p:
        c, n = p
        return c * n * x**n


def d_forgot_coefficient(f):         # x^3 -> x^2
    p = _coef_power(f)
    if p:
        c, n = p
        return c * x**(n - 1)


def d_forgot_chain_rule(f):          # sin(2x) -> cos(2x), (3x+1)^4 -> 4(3x+1)^3
    if len(f.args) == 1 and f.args[0] != x and f.args[0].has(x):
        u = Dummy("u")
        return f.func(u).diff(u).subs(u, f.args[0])
    if f.is_Pow and f.base != x and f.base.has(x) and not f.exp.has(x):
        return f.exp * f.base ** (f.exp - 1)


def d_forgot_product_rule(f):        # u*v -> u'*v'  (differentiated each factor and multiplied)
    if f.is_Mul:
        factors = [a for a in f.args if a.has(x)]
        if len(factors) == 2:
            u, v = factors
            const = f / (u * v)
            return const * u.diff(x) * v.diff(x)


# ---------- integral bugs ----------

def i_no_division(f):                # x^2 -> x^3
    p = _coef_power(f)
    if p:
        c, n = p
        return c * x**(n + 1)


def i_differentiated(f):             # integrated by differentiating
    return f.diff(x)


def i_sign_error(f):                 # integral of cos(x) -> -sin(x)
    return -integrate(f, x)


D_BUGS = {
    "POWER_NOT_REDUCED": d_power_not_reduced,
    "FORGOT_COEFFICIENT": d_forgot_coefficient,
    "FORGOT_CHAIN_RULE": d_forgot_chain_rule,
    "FORGOT_PRODUCT_RULE": d_forgot_product_rule,
}
I_BUGS = {
    "FORGOT_TO_DIVIDE_BY_NEW_POWER": i_no_division,
    "DIFFERENTIATED_INSTEAD": i_differentiated,
    "SIGN_ERROR": i_sign_error,
}


def _strip_c(s: str):
    t = s.strip()
    u = re.sub(r"\+\s*[cC]\s*$", "", t)
    return u, u != t


def _same(a, b, up_to_constant):
    d = simplify(a - b)
    return (not d.has(x)) if up_to_constant else d == 0


def check(kind: str, expression: str, answer: str) -> dict:
    """kind is 'derivative' or 'integral'."""
    f = parse(expression)
    text, has_c = _strip_c(clean(answer))
    s = parse(text)
    prev = ("derivative of " if kind == "derivative" else "integral of ") + expression

    if kind == "derivative":
        correct = simplify(s - f.diff(x)) == 0
        bugs, const = D_BUGS, False
    else:
        correct = simplify(s.diff(x) - f) == 0
        bugs, const = I_BUGS, True

    if correct and (kind == "derivative" or has_c):
        return {"status": "correct", "subject": kind}

    if correct:                      # right maths, but no + C
        tag = "FORGOT_PLUS_C"
    else:
        tag = "UNKNOWN"
        for name, fn in bugs.items():
            try:
                cand = fn(f)
            except Exception:
                cand = None
            if cand is not None and _same(cand, s, const):
                tag = name
                break
    return {"status": "wrong", "subject": kind, "tag": tag,
            "prev": prev, "wrong": answer}


def make_problem(kind: str, tag: str) -> str:
    a, b, n = random.randint(2, 6), random.randint(1, 5), random.randint(2, 5)
    if kind == "derivative":
        if tag == "FORGOT_CHAIN_RULE":
            return f"({a}x + {b})^{n}"
        if tag == "FORGOT_PRODUCT_RULE":
            return f"x^{n} sin(x)"
        return f"{a}x^{n}"
    if tag == "SIGN_ERROR":
        return random.choice(["sin(x)", "cos(x)"])
    return f"{a}x^{n}"


EXPLANATIONS = {
    "POWER_NOT_REDUCED": (
        "The power rule has two parts: bring the power down in front, then lower the power by 1.",
        "After you bring the 3 down from x^3, what should the new power be?"),
    "FORGOT_COEFFICIENT": (
        "The power rule also brings the old power down in front as a multiplier.",
        "What happens to the old power when you differentiate x^n?"),
    "FORGOT_CHAIN_RULE": (
        "When one function sits inside another, you also multiply by the derivative of the inside part.",
        "What is the derivative of the inside part?"),
    "FORGOT_PRODUCT_RULE": (
        "For two functions multiplied together, you can't differentiate each and multiply. "
        "The product rule is: (first)' x second + first x (second)'.",
        "What are the two terms you get when you apply the product rule to u times v?"),
    "FORGOT_TO_DIVIDE_BY_NEW_POWER": (
        "Integrating raises the power by 1 and then divides by that new power.",
        "If you differentiate your answer, do you get the original back?"),
    "SIGN_ERROR": (
        "Watch the signs: the integral of cos is sin, but the integral of sin is negative cos.",
        "Differentiate your answer. Does the sign match the original?"),
    "DIFFERENTIATED_INSTEAD": (
        "Integration is the reverse of differentiation, so it should go the other way.",
        "Which operation turns x^3 into x^2: differentiating or integrating?"),
    "FORGOT_PLUS_C": (
        "Your integral is right, but an indefinite integral needs + C, because many functions share one derivative.",
        "What is the derivative of a constant like 5?"),
}