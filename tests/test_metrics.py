"""
Tests para el sistema de métricas en memoria de MEDI-IA.
Cubre: _record_query, _record_error, /api/metrics endpoint y distribución horaria.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import pytest
from unittest.mock import patch

import app as app_mod

flask_app = app_mod.app


@pytest.fixture(autouse=True)
def reset_metrics():
    """Limpia las métricas en memoria antes y después de cada test."""
    with app_mod._mtx:
        app_mod._query_ts.clear()
        app_mod._lat_log.clear()
        app_mod._err_count[0] = 0
    yield
    with app_mod._mtx:
        app_mod._query_ts.clear()
        app_mod._lat_log.clear()
        app_mod._err_count[0] = 0


@pytest.fixture
def client(tmp_path, monkeypatch):
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_metrics.db"))
    mem_mod._init_schema()

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as c:
        yield c


# ─── _record_query / _record_error ────────────────────────────────────────────

class TestRecordHelpers:
    def test_record_query_increments_ts(self):
        assert len(app_mod._query_ts) == 0
        app_mod._record_query(200)
        assert len(app_mod._query_ts) == 1

    def test_record_query_stores_latency(self):
        app_mod._record_query(350)
        assert len(app_mod._lat_log) == 1
        _ts, ms = app_mod._lat_log[0]
        assert ms == 350

    def test_record_query_multiple(self):
        for ms in [100, 200, 300]:
            app_mod._record_query(ms)
        assert len(app_mod._query_ts) == 3
        assert len(app_mod._lat_log) == 3

    def test_record_error_increments_count(self):
        assert app_mod._err_count[0] == 0
        app_mod._record_error()
        assert app_mod._err_count[0] == 1

    def test_record_error_multiple(self):
        app_mod._record_error()
        app_mod._record_error()
        app_mod._record_error()
        assert app_mod._err_count[0] == 3

    def test_record_query_ts_is_recent(self):
        before = time.time()
        app_mod._record_query(100)
        after = time.time()
        ts = app_mod._query_ts[0]
        assert before <= ts <= after


# ─── /api/metrics ─────────────────────────────────────────────────────────────

class TestMetricsEndpoint:
    def test_returns_200(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        assert r.status_code == 200

    def test_required_fields_present(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        required = [
            "queries_last_1h", "queries_last_24h", "queries_session_total",
            "avg_latency_ms", "p95_latency_ms", "error_count",
            "uptime_s", "hourly_last_24h", "hourly_labels",
            "feedback_total", "feedback_positive", "feedback_negative",
        ]
        for field in required:
            assert field in data, f"Campo faltante: {field}"

    def test_hourly_last_24h_has_24_buckets(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert len(data["hourly_last_24h"]) == 24

    def test_hourly_labels_has_24_entries(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert len(data["hourly_labels"]) == 24

    def test_zero_queries_returns_zero_counts(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["queries_last_1h"] == 0
        assert data["queries_last_24h"] == 0
        assert data["queries_session_total"] == 0
        assert data["avg_latency_ms"] == 0
        assert data["p95_latency_ms"] == 0

    def test_error_count_zero_initially(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["error_count"] == 0

    def test_uptime_s_is_positive(self, client):
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["uptime_s"] >= 0

    def test_query_count_reflects_records(self, client):
        app_mod._record_query(150)
        app_mod._record_query(250)
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["queries_session_total"] == 2
        assert data["queries_last_1h"] == 2
        assert data["queries_last_24h"] == 2

    def test_avg_latency_computed_correctly(self, client):
        app_mod._record_query(100)
        app_mod._record_query(300)
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["avg_latency_ms"] == 200

    def test_error_count_reflected_in_metrics(self, client):
        app_mod._record_error()
        app_mod._record_error()
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["error_count"] == 2

    def test_feedback_stats_included(self, client):
        with patch.object(app_mod, "get_feedback_stats",
                          return_value={"total": 10, "positive": 8, "negative": 2}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["feedback_total"] == 10
        assert data["feedback_positive"] == 8
        assert data["feedback_negative"] == 2

    def test_recent_query_counted_in_1h_bucket(self, client):
        app_mod._record_query(500)
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        # La query recién registrada debe aparecer en el bucket más reciente (índice 23)
        assert data["hourly_last_24h"][23] >= 1

    def test_p95_latency_with_multiple_records(self, client):
        # 20 records: 19 de 100ms y 1 de 1000ms — p95 debe ser >= 100
        for _ in range(19):
            app_mod._record_query(100)
        app_mod._record_query(1000)
        with patch.object(app_mod, "get_feedback_stats", return_value={"total": 0, "positive": 0, "negative": 0}):
            r = client.get("/api/metrics")
        data = r.get_json()
        assert data["p95_latency_ms"] >= 100
