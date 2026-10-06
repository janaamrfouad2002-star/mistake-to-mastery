from sympy import Eq, simplify
from app.checker import parse_equation, parse_equation_raw, x

def _linear_parts(L):
    """For a*x + b -> (a, b). Returns None if not that shape."""
    b, dep = L.as_independent(x, as_Add=True)
    a = dep.coeff(x)
    if a == 0:
        return None
    return a, b


def sign_error(L, R):          # ax + b = c  ->  ax = c + b  (should be c - b)
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(a * x, R + b)


def forgot_to_divide(L, R):    # ax + b = c -> x = c - b
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(x, R - b)


def multiplied_instead_of_divided(L, R):   # ax + b = c -> x = (c-b)*a
    p = _linear_parts(L)
    if p:
        a, b = p
        return Eq(x, (R - b) * a)


def forgot_to_distribute(L, R):   # k(x+m) = c -> kx + m = c
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