from langchain_core.language_models.fake_chat_models import FakeListChatModel
from sympy import solve
from app.engine import Extracted, analyse, make_twin
from app import core, llm
from app.core import (first_wrong_step, diagnose, make_problem,
                      parse_equation, x, record, mistake_map)


# ---- checker and bug library ----
def test_sign_error():
    steps = ["2x + 3 = 11", "2x = 14", "x = 7"]
    i = first_wrong_step(steps)
    assert i == 1
    assert diagnose(steps[0], steps[i]) == "SIGN_ERROR_MOVING_TERM"


def test_correct_solution():
    assert first_wrong_step(["2x + 3 = 11", "2x = 8", "x = 4"]) is None


def test_distribute():
    assert diagnose("3(x + 4) = 21", "3x + 4 = 21") == "FORGOT_TO_DISTRIBUTE"


def test_forgot_to_divide():
    assert diagnose("2x + 3 = 11", "x = 8") == "FORGOT_TO_DIVIDE"


def test_multiplied_instead_of_divided():
    assert diagnose("2x + 3 = 11", "x = 16") == "MULTIPLIED_INSTEAD_OF_DIVIDED"


# ---- twin generator and memory ----
def test_twin_has_whole_number_answer():
    for tag in ["SIGN_ERROR_MOVING_TERM", "FORGOT_TO_DISTRIBUTE"]:
        for _ in range(20):
            sol = solve(parse_equation(make_problem(tag)), x)
            assert len(sol) == 1 and sol[0].is_integer


def test_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "DB", str(tmp_path / "t.db"))
    record("jana", "SIGN_ERROR_MOVING_TERM", correct=False)
    assert mistake_map("jana")[0][1] == 1
    record("jana", "SIGN_ERROR_MOVING_TERM", correct=True)
    assert mistake_map("jana")[0][2] == 1


# ---- AI layer, with the Gemini connection replaced by a fake ----
def test_llm_uses_model_when_available(monkeypatch):
    monkeypatch.setattr(llm, "_get_model",
                        lambda: FakeListChatModel(responses=["Fake Gemini hint"]))
    assert llm.explain_with_llm("a", "b", "SIGN_ERROR_MOVING_TERM") == "Fake Gemini hint"


def test_llm_falls_back_to_templates(monkeypatch):
    monkeypatch.setattr(llm, "_get_model", lambda: None)
    out = llm.explain_with_llm("a", "b", "FORGOT_TO_DISTRIBUTE")
    assert "brackets" in out


def test_engine_algebra():
    r = analyse(Extracted(subject="algebra", steps=["2x + 3 = 11", "2x = 14", "x = 7"]))
    assert r["tag"] == "SIGN_ERROR_MOVING_TERM"


def test_derivative_correct():
    r = analyse(Extracted(subject="derivative", expression="x^3", student_answer="3x^2"))
    assert r["status"] == "correct"


def test_derivative_power_not_reduced():
    r = analyse(Extracted(subject="derivative", expression="x^3", student_answer="3x^3"))
    assert r["tag"] == "POWER_NOT_REDUCED"


def test_derivative_forgot_chain_rule():
    r = analyse(Extracted(subject="derivative", expression="sin(2x)", student_answer="cos(2x)"))
    assert r["tag"] == "FORGOT_CHAIN_RULE"


def test_integral_no_division():
    r = analyse(Extracted(subject="integral", expression="x^2", student_answer="x^3 + C"))
    assert r["tag"] == "FORGOT_TO_DIVIDE_BY_NEW_POWER"


def test_integral_forgot_plus_c():
    r = analyse(Extracted(subject="integral", expression="2x", student_answer="x^2"))
    assert r["tag"] == "FORGOT_PLUS_C"


def test_integral_correct():
    r = analyse(Extracted(subject="integral", expression="2x", student_answer="x^2 + C"))
    assert r["status"] == "correct"


def test_calculus_twins_can_be_checked():
    for kind, tag in [("derivative", "FORGOT_CHAIN_RULE"), ("integral", "SIGN_ERROR")]:
        p = make_twin(kind, tag)
        r = analyse(Extracted(subject=kind, expression=p, student_answer="0"))
        assert r["status"] == "wrong"


def test_extract_offline_fallback(monkeypatch):
    monkeypatch.setattr(llm, "_get_model", lambda: None)
    ex = llm.extract("2x + 3 = 11\n2x = 14")
    assert ex.subject == "algebra" and len(ex.steps) == 2

def test_question_only_gets_solved():
    r = analyse(Extracted(subject="derivative", expression="x^3"))
    assert r["status"] == "solved" and r["answer"] == "3*x**2"


def test_integral_question_only():
    r = analyse(Extracted(subject="integral", expression="2x"))
    assert r["status"] == "solved" and "x**2" in r["answer"]
