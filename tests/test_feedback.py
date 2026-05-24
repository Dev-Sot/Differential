"""
Tests para el sistema de feedback de MEDI-IA.
Cubre: save_feedback / get_feedback_stats (memory.py) y POST /api/feedback (endpoint).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch

import app as app_mod

flask_app = app_mod.app


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Base de datos SQLite temporal con esquema inicializado."""
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_feedback.db"))
    mem_mod._init_schema()
    return mem_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_feedback_api.db"))
    mem_mod._init_schema()

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as c:
        yield c


# ─── save_feedback / get_feedback_stats ───────────────────────────────────────

class TestFeedbackMemory:
    def test_stats_empty_initially(self, db):
        stats = db.get_feedback_stats()
        assert stats["total"] == 0
        assert stats["positive"] == 0
        assert stats["negative"] == 0

    def test_save_positive_feedback(self, db):
        db.save_feedback("sess-001", "Gripe", 1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 1
        assert stats["positive"] == 1
        assert stats["negative"] == 0

    def test_save_negative_feedback(self, db):
        db.save_feedback("sess-001", "Gripe", -1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 1
        assert stats["positive"] == 0
        assert stats["negative"] == 1

    def test_save_multiple_feedback(self, db):
        db.save_feedback("sess-001", "Gripe", 1)
        db.save_feedback("sess-001", "Gripe", 1)
        db.save_feedback("sess-002", "Migraña", -1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 3
        assert stats["positive"] == 2
        assert stats["negative"] == 1

    def test_feedback_from_different_sessions(self, db):
        for i in range(5):
            db.save_feedback(f"sess-{i}", "Condicion", 1)
        db.save_feedback("sess-X", "Otra", -1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 6
        assert stats["positive"] == 5
        assert stats["negative"] == 1

    def test_save_feedback_empty_condicion(self, db):
        db.save_feedback("sess-001", "", 1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 1

    def test_save_feedback_none_condicion(self, db):
        db.save_feedback("sess-001", None, -1)
        stats = db.get_feedback_stats()
        assert stats["total"] == 1
        assert stats["negative"] == 1

    def test_stats_returns_dict_with_required_keys(self, db):
        stats = db.get_feedback_stats()
        assert "total" in stats
        assert "positive" in stats
        assert "negative" in stats

    def test_total_equals_positive_plus_negative(self, db):
        db.save_feedback("s1", "A", 1)
        db.save_feedback("s2", "B", -1)
        db.save_feedback("s3", "C", 1)
        stats = db.get_feedback_stats()
        assert stats["total"] == stats["positive"] + stats["negative"]


# ─── POST /api/feedback ────────────────────────────────────────────────────────

class TestFeedbackEndpoint:
    def test_missing_rating_returns_400(self, client):
        r = client.post("/api/feedback", json={"condicion": "Gripe"})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_empty_body_returns_400(self, client):
        r = client.post("/api/feedback", json={})
        assert r.status_code == 400

    def test_invalid_rating_zero_returns_400(self, client):
        r = client.post("/api/feedback", json={"rating": 0})
        assert r.status_code == 400
        data = r.get_json()
        assert "error" in data
        assert "rating" in data["error"].lower()

    def test_invalid_rating_string_returns_400(self, client):
        r = client.post("/api/feedback", json={"rating": "bueno"})
        assert r.status_code == 400

    def test_invalid_rating_2_returns_400(self, client):
        r = client.post("/api/feedback", json={"rating": 2})
        assert r.status_code == 400

    def test_positive_rating_1_returns_200(self, client):
        r = client.post("/api/feedback", json={"rating": 1, "condicion": "Gripe"})
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("ok") is True

    def test_negative_rating_minus1_returns_200(self, client):
        r = client.post("/api/feedback", json={"rating": -1, "condicion": "Migraña"})
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("ok") is True

    def test_feedback_without_condicion_returns_200(self, client):
        r = client.post("/api/feedback", json={"rating": 1})
        assert r.status_code == 200

    def test_feedback_persisted_in_db(self, client):
        import src.memory as mem_mod
        r = client.post("/api/feedback", json={"rating": 1, "condicion": "Gripe viral"})
        assert r.status_code == 200
        stats = mem_mod.get_feedback_stats()
        assert stats["total"] >= 1
        assert stats["positive"] >= 1

    def test_negative_feedback_persisted_in_db(self, client):
        import src.memory as mem_mod
        r = client.post("/api/feedback", json={"rating": -1, "condicion": "Apendicitis"})
        assert r.status_code == 200
        stats = mem_mod.get_feedback_stats()
        assert stats["negative"] >= 1

    def test_feedback_reflected_in_metrics(self, client):
        with app_mod._mtx:
            app_mod._query_ts.clear()
            app_mod._lat_log.clear()
            app_mod._err_count[0] = 0

        client.post("/api/feedback", json={"rating": 1})
        client.post("/api/feedback", json={"rating": 1})
        client.post("/api/feedback", json={"rating": -1})

        r = client.get("/api/metrics")
        assert r.status_code == 200
        data = r.get_json()
        assert data["feedback_total"] >= 3
        assert data["feedback_positive"] >= 2
        assert data["feedback_negative"] >= 1

    def test_save_feedback_error_returns_500(self, client):
        with patch.object(app_mod, "save_feedback", side_effect=Exception("db error")):
            r = client.post("/api/feedback", json={"rating": 1})
        assert r.status_code == 500
        assert "error" in r.get_json()
