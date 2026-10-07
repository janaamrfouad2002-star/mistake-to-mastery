from langchain_core.language_models.fake_chat_models import FakeListChatModel
from sympy import solve

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