import random


def make_problem(tag: str) -> str:
    x0 = random.randint(-9, 9)           # the secret answer, chosen first
    a = random.choice([2, 3, 4, 5, 6])   # multiplier
    b = random.randint(2, 9)             # number added
    if tag == "FORGOT_TO_DISTRIBUTE":
        return f"{a}(x + {b}) = {a * (x0 + b)}"
    c = a * x0 + b                       # build the right side from the answer
    return f"{a}x + {b} = {c}"