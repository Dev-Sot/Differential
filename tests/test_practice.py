"""
Tests para el modo de practica de casos (src/practice.py + rutas /api/practice/*).
Cubre el banco de casos, evaluacion (modo autoevaluacion, sin HF_TOKEN),
persistencia de intentos y las rutas Flask protegidas.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

import app as app_mod
import src.auth as auth_mod
import src.practice as practice_mod

flask_app = app_mod.app


@pytest.fixture
def db(tmp_path, monkeypatch):
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_practice.db"))
    mem_mod._init_schema()
    auth_mod._init_schema()
    practice_mod._init_schema()
    return practice_mod


@pytest.fixture
def user_id(db):
    return auth_mod.create_user("test@example.com", "password123")


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    user_id = auth_mod.create_user("client@example.com", "password123")
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.config["RATELIMIT_ENABLED"] = False
    with flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = user_id
        yield c


# ─── Banco de casos ─────────────────────────────────────────────────────────

class TestCaseBank:
    def test_case_bank_loads(self):
        cases = practice_mod._load_cases()
        assert len(cases) >= 10

    def test_every_case_has_required_fields(self):
        for case in practice_mod._load_cases():
            for field in ("id", "specialty", "vignette", "reference_differential", "correct_dx", "teaching_point"):
                assert field in case, f"falta '{field}' en el caso {case.get('id')}"

    def test_case_ids_are_unique(self):
        cases = practice_mod._load_cases()
        ids = [c["id"] for c in cases]
        assert len(ids) == len(set(ids))

    def test_get_case_by_id(self):
        cases = practice_mod._load_cases()
        found = practice_mod.get_case(cases[0]["id"])
        assert found is not None
        assert found["id"] == cases[0]["id"]

    def test_get_case_unknown_id_returns_none(self):
        assert practice_mod.get_case("no-existe-123") is None

    def test_get_random_case_respects_exclude(self):
        all_ids = [c["id"] for c in practice_mod._load_cases()]
        exclude = all_ids[:-1]  # excluir todos menos uno
        case = practice_mod.get_random_case(exclude_ids=exclude)
        assert case["id"] == all_ids[-1]

    def test_public_case_hides_answer(self):
        case = practice_mod._load_cases()[0]
        public = practice_mod.public_case(case)
        assert "correct_dx" not in public
        assert "reference_differential" not in public
        assert "teaching_point" not in public
        assert public["vignette"] == case["vignette"]


# ─── evaluate_answer (sin HF_TOKEN -> autoevaluacion) ──────────────────────

class TestEvaluateAnswer:
    def test_self_assessment_mode_without_token(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        case = practice_mod._load_cases()[0]
        result = practice_mod.evaluate_answer(case, "mi respuesta")
        assert result["mode"] == "self_assessment"
        assert result["correct_dx"] == case["correct_dx"]
        assert result["reference_differential"] == case["reference_differential"]
        assert result["teaching_point"] == case["teaching_point"]


# ─── Persistencia: record_attempt / rate_attempt / get_progress ───────────

class TestProgress:
    def test_record_attempt_returns_id(self, db, user_id):
        attempt_id = db.record_attempt(user_id, "cardio-01", "Cardiología", "mi respuesta", "self_assessment")
        assert isinstance(attempt_id, int)

    def test_progress_empty_initially(self, db, user_id):
        p = db.get_progress(user_id)
        assert p["total_attempts"] == 0
        assert p["accuracy"] is None

    def test_progress_counts_attempts(self, db, user_id):
        db.record_attempt(user_id, "cardio-01", "Cardiología", "resp1", "self_assessment")
        db.record_attempt(user_id, "neuro-01", "Neurología", "resp2", "self_assessment")
        p = db.get_progress(user_id)
        assert p["total_attempts"] == 2

    def test_rate_attempt_updates_rating(self, db, user_id):
        attempt_id = db.record_attempt(user_id, "cardio-01", "Cardiología", "resp", "self_assessment")
        ok = db.rate_attempt(attempt_id, user_id, "correct")
        assert ok is True
        p = db.get_progress(user_id)
        assert p["rated_attempts"] == 1
        assert p["accuracy"] == 1.0

    def test_rate_attempt_wrong_user_fails(self, db, user_id):
        attempt_id = db.record_attempt(user_id, "cardio-01", "Cardiología", "resp", "self_assessment")
        ok = db.rate_attempt(attempt_id, user_id + 999, "correct")
        assert ok is False

    def test_accuracy_computed_from_rated_only(self, db, user_id):
        a1 = db.record_attempt(user_id, "cardio-01", "Cardiología", "r1", "self_assessment")
        db.record_attempt(user_id, "neuro-01", "Neurología", "r2", "self_assessment")  # sin calificar
        db.rate_attempt(a1, user_id, "correct")
        p = db.get_progress(user_id)
        assert p["total_attempts"] == 2
        assert p["rated_attempts"] == 1
        assert p["accuracy"] == 1.0


# ─── Rutas Flask ────────────────────────────────────────────────────────────

class TestPracticeRoutes:
    def test_practice_page_requires_auth(self):
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            r = c.get("/practice")
            assert r.status_code == 302

    def test_get_case_returns_public_fields_only(self, client):
        r = client.get("/api/practice/case")
        assert r.status_code == 200
        data = r.get_json()
        assert "vignette" in data
        assert "correct_dx" not in data

    def test_submit_without_answer_returns_400(self, client):
        r = client.get("/api/practice/case")
        case_id = r.get_json()["id"]
        r2 = client.post("/api/practice/submit", json={"case_id": case_id, "answer": ""})
        assert r2.status_code == 400

    def test_submit_unknown_case_returns_404(self, client):
        r = client.post("/api/practice/submit", json={"case_id": "no-existe", "answer": "algo"})
        assert r.status_code == 404

    def test_submit_valid_answer_returns_self_assessment(self, client):
        r = client.get("/api/practice/case")
        case_id = r.get_json()["id"]
        r2 = client.post("/api/practice/submit", json={"case_id": case_id, "answer": "Mi diferencial es X"})
        assert r2.status_code == 200
        data = r2.get_json()
        assert data["mode"] == "self_assessment"
        assert "attempt_id" in data
        assert "correct_dx" in data

    def test_rate_endpoint_persists_rating(self, client):
        r = client.get("/api/practice/case")
        case_id = r.get_json()["id"]
        r2 = client.post("/api/practice/submit", json={"case_id": case_id, "answer": "respuesta"})
        attempt_id = r2.get_json()["attempt_id"]

        r3 = client.post("/api/practice/rate", json={"attempt_id": attempt_id, "self_rating": "correct"})
        assert r3.status_code == 200

    def test_rate_endpoint_rejects_invalid_rating(self, client):
        r = client.post("/api/practice/rate", json={"attempt_id": 1, "self_rating": "mas-o-menos"})
        assert r.status_code == 400

    def test_progress_endpoint_returns_summary(self, client):
        r = client.get("/api/practice/progress")
        assert r.status_code == 200
        data = r.get_json()
        assert "total_attempts" in data
        assert "accuracy" in data
