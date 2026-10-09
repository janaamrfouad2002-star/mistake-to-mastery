from sympy import solve
from app.checker import parse_equation, x
from app.generator import make_problem
from app import memory


def test_twin_has_whole_number_answer():
    for tag in ["SIGN_ERROR_MOVING_TERM", "FORGOT_TO_DISTRIBUTE"]:
        for _ in range(20):
            sol = solve(parse_equation(make_problem(tag)), x)
            assert len(sol) == 1 and sol[0].is_integer


def test_memory_tracks_errors_and_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DB", str(tmp_path / "test.db"))  # temporary database
    memory.record("jana", "SIGN_ERROR_MOVING_TERM", correct=False)
    assert memory.mistake_map("jana")[0][1] == 1     # 1 error recorded
    memory.record("jana", "SIGN_ERROR_MOVING_TERM", correct=True)
    assert memory.mistake_map("jana")[0][2] == 1     # moved up to box 1