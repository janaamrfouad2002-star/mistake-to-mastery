from sympy import Eq, symbols, solve, simplify
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)

x = symbols("x")
T = standard_transformations + (implicit_multiplication_application,)


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
    """Returns index of first incorrect step (>=1), or None if all valid."""
    for i in range(1, len(steps)):
        if not equivalent(steps[i - 1], steps[i]):
            return i
    return None