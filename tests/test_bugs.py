from app.checker import first_wrong_step
from app.bugs import diagnose


def test_sign_error():
    steps = ["2x + 3 = 11", "2x = 14", "x = 7"]
    i = first_wrong_step(steps)
    assert i == 1
    assert diagnose(steps[0], steps[i]) == "SIGN_ERROR_MOVING_TERM"


def test_correct_solution():
    assert first_wrong_step(["2x + 3 = 11", "2x = 8", "x = 4"]) is None


def test_distribute():
    steps = ["3(x + 4) = 21", "3x + 4 = 21"]
    assert diagnose(steps[0], steps[1]) == "FORGOT_TO_DISTRIBUTE"