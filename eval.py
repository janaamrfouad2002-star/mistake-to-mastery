"""eval.py - measures how well the mistake detector works."""
import random
from collections import Counter

from app.core import first_wrong_step, diagnose

N = 100   # cases per mistake type
random.seed(1)

TAGS = ["SIGN_ERROR_MOVING_TERM", "FORGOT_TO_DIVIDE",
        "MULTIPLIED_INSTEAD_OF_DIVIDED", "FORGOT_TO_DISTRIBUTE"]


def make_case(tag):
    """Returns [correct previous step, buggy next step] for one mistake type."""
    x0 = random.randint(-9, 9)
    a, b = random.randint(2, 9), random.randint(2, 9)
    if tag == "FORGOT_TO_DISTRIBUTE":
        c = a * (x0 + b)
        return [f"{a}(x + {b}) = {c}", f"{a}x + {b} = {c}"]
    c = a * x0 + b
    wrong = {
        "SIGN_ERROR_MOVING_TERM": f"{a}x = {c + b}",
        "FORGOT_TO_DIVIDE": f"x = {c - b}",
        "MULTIPLIED_INSTEAD_OF_DIVIDED": f"x = {(c - b) * a}",
    }[tag]
    return [f"{a}x + {b} = {c}", wrong]


results = {}
for tag in TAGS:
    hits, skipped = 0, 0
    confusions = Counter()
    for _ in range(N):
        steps = make_case(tag)
        if first_wrong_step(steps) is None:     # the "bug" happened to be correct (e.g. x = 0)
            skipped += 1
            continue
        pred = diagnose(steps[0], steps[1])
        confusions[pred] += 1
        hits += pred == tag
    used = N - skipped
    results[tag] = (hits, used, skipped, confusions)

# False alarms: fully correct solutions should never be flagged
false_alarms = 0
for _ in range(N):
    x0 = random.randint(-9, 9)
    a, b = random.randint(2, 9), random.randint(2, 9)
    c = a * x0 + b
    steps = [f"{a}x + {b} = {c}", f"{a}x = {c - b}", f"x = {x0}"]
    false_alarms += first_wrong_step(steps) is not None

print(f"\n{'Mistake type':32}{'Correct':>9}{'Total':>7}{'Accuracy':>10}")
for tag, (hits, used, skipped, conf) in results.items():
    print(f"{tag:32}{hits:>9}{used:>7}{hits / used:>10.0%}")
    if hits < used:
        print(f"   predicted instead: {dict(conf)}")
total_hits = sum(r[0] for r in results.values())
total_used = sum(r[1] for r in results.values())
print(f"\nOverall: {total_hits}/{total_used} = {total_hits / total_used:.1%}")
print(f"False alarms on correct solutions: {false_alarms}/{N}")