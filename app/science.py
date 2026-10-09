"""science.py - verifier modules for chemistry (balancing) and physics (units). No AI."""
import random
import re
from collections import Counter
from math import gcd
from functools import reduce

import pint
from sympy import Matrix, ilcm

ureg = pint.UnitRegistry()

# ---------------- CHEMISTRY ----------------

def parse_formula(f: str) -> Counter:
    """'Ca(OH)2' -> Counter({'Ca': 1, 'O': 2, 'H': 2})"""
    tokens = re.findall(r"[A-Z][a-z]?|\(|\)|\d+", f)
    stack = [Counter()]
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "(":
            stack.append(Counter())
        elif t == ")":
            group = stack.pop()
            n = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                n = int(tokens[i + 1])
                i += 1
            for k, v in group.items():
                stack[-1][k] += v * n
        elif not t.isdigit():
            n = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                n = int(tokens[i + 1])
                i += 1
            stack[-1][t] += n
        i += 1
    return stack[0]


def _terms(side: str):
    out = []
    for t in side.split("+"):
        t = t.strip()
        if not t:
            continue
        m = re.match(r"^(\d+)\s*(.+)$", t)
        out.append((int(m.group(1)), m.group(2).strip()) if m else (1, t))
    return out


def _sides(eq: str):
    eq = eq.replace("→", "->")
    left, right = eq.split("->" if "->" in eq else "=")
    return _terms(left), _terms(right)


def _count(side):
    c = Counter()
    for coef, sp in side:
        for el, n in parse_formula(sp).items():
            c[el] += coef * n
    return c


def _solve(left_names, right_names):
    species = left_names + right_names
    elems = sorted({e for s in species for e in parse_formula(s)})
    rows = [[parse_formula(s)[e] for s in left_names] +
            [-parse_formula(s)[e] for s in right_names] for e in elems]
    ns = Matrix(rows).nullspace()
    if len(ns) != 1:
        return None
    v = ns[0]
    mult = ilcm(*[x.q for x in v])
    v = [int(x * mult) for x in v]
    if v[0] < 0:
        v = [-x for x in v]
    if any(x <= 0 for x in v):
        return None
    g = reduce(gcd, v)
    return [x // g for x in v]


def balance_equation(eq: str) -> str:
    L, R = _sides(eq)
    ln, rn = [s for _, s in L], [s for _, s in R]
    sol = _solve(ln, rn)
    if sol is None:
        return "no simple balance found"
    fmt = lambda c, s: f"{c}{s}" if c > 1 else s
    left = " + ".join(fmt(c, s) for c, s in zip(sol[:len(ln)], ln))
    right = " + ".join(fmt(c, s) for c, s in zip(sol[len(ln):], rn))
    return f"{left} -> {right}"


def check_balance(eq: str) -> dict:
    L, R = _sides(eq)
    cl, cr = _count(L), _count(R)
    if cl == cr:
        return {"status": "correct", "subject": "chemistry_balance"}
    diff = ", ".join(f"{e}: {cl[e]} left vs {cr[e]} right"
                     for e in sorted(set(cl) | set(cr)) if cl[e] != cr[e])
    return {"status": "wrong", "subject": "chemistry_balance",
            "tag": "ATOMS_NOT_CONSERVED",
            "prev": f"Atom count mismatch: {diff}", "wrong": eq}


CHEM_TWINS = ["H2 + O2 -> H2O", "N2 + H2 -> NH3", "Fe + O2 -> Fe2O3",
              "C3H8 + O2 -> CO2 + H2O", "Al + HCl -> AlCl3 + H2", "CH4 + O2 -> CO2 + H2O"]


def make_chem_twin() -> str:
    return random.choice(CHEM_TWINS)


def check_chem_twin(problem: str, student: str) -> bool:
    try:
        same = ({s for _, s in sum(_sides(problem), [])} ==
                {s for _, s in sum(_sides(student), [])})
        return same and check_balance(student)["status"] == "correct"
    except Exception:
        return False

# ---------------- PHYSICS ----------------

def _q(s: str):
    return ureg.Quantity(ureg.parse_expression(s))


_RATIOS = [10, 100, 1000, 60, 3600, 0.1, 0.01, 0.001, 1 / 60, 1 / 3600]


def check_calc(expression: str, answer: str) -> dict:
    """expression like '20 m / (4 s)', answer like '5 m/s'."""
    q, s = _q(expression), _q(answer)
    base = {"subject": "physics_calc", "prev": f"{expression} = ?", "wrong": answer}
    if q.dimensionality != s.dimensionality:
        return {**base, "status": "wrong", "tag": "WRONG_UNITS"}
    qb, sb = q.to_base_units().magnitude, s.to_base_units().magnitude
    if abs(qb - sb) <= 0.01 * abs(qb):
        return {"status": "correct", "subject": "physics_calc"}
    if qb != 0 and any(abs(sb / qb - r) < 1e-6 * max(1, r) for r in _RATIOS):
        return {**base, "status": "wrong", "tag": "UNIT_CONVERSION_ERROR"}
    return {**base, "status": "wrong", "tag": "WRONG_VALUE"}


def solve_calc(expression: str) -> str:
    q = _q(expression).to_base_units()
    return f"{q:~P}"


def make_phys_twin() -> str:
    a, b = random.randint(2, 9), random.randint(2, 9)
    return f"{a * b} m / ({b} s)"


EXPLANATIONS = {
    "ATOMS_NOT_CONSERVED": (
        "Atoms can't appear or disappear in a reaction, so each element must have the "
        "same count on both sides. Change the big numbers in front (coefficients), never the small ones inside a formula.",
        "Which element has a different count on each side, and which formula can you multiply to fix it?"),
    "WRONG_UNITS": (
        "Your number may be fine, but the units don't match the quantity being asked for.",
        "What unit should the answer have, for example metres per second for speed?"),
    "UNIT_CONVERSION_ERROR": (
        "Your answer is off by a factor that looks like a unit conversion, such as 1000 or 60.",
        "How many metres are in a kilometre, and did you multiply or divide?"),
    "WRONG_VALUE": (
        "The units are right but the number isn't.",
        "Which formula connects these quantities, and did you substitute each value into the right place?"),
}