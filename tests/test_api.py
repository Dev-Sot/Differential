"""
Tests de integracion para los endpoints Flask de MEDI-IA.
Mockean run(), get_health() y WeasyPrint para no depender de FAISS ni HF.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import types
import pytest
from unittest.mock import patch, MagicMock

import app as app_mod

flask_app = app_mod.app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente de test Flask con SQLite temporal para la memoria."""
    import src.memory as mem_mod
    monkeypatch.setattr(mem_mod, "DB_PATH", str(tmp_path / "test_api.db"))
    mem_mod._init_schema()

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as c:
        yield c


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fake_run_result(gravedad="leve"):
    return {
        "respuesta": "El paciente presenta sindrome gripal.",
        "gravedad": gravedad,
        "gravedad_info": {
            "label": gravedad.upper(),
            "color": "#22c55e",
            "icon": "🟢",
            "description": "No urgente",
        },
        "condicion_principal": "Sindrome gripal",
        "recomendacion": "Reposo y liquidos.",
        "condiciones_relacionadas": [],
        "urgencia": gravedad,
        "score_confianza": 70,
        "fuentes": ["Harrison"],
        "modo": "RAG Template",
        "trajectory": [],
        "tools_used": [],
    }


def _fake_weasyprint_module():
    """Modulo weasyprint falso que devuelve bytes PDF validos."""
    fake_mod = types.ModuleType("weasyprint")
    instance = MagicMock()
    instance.write_pdf.return_value = b"%PDF-1.4 fake-content"
    fake_mod.HTML = MagicMock(return_value=instance)
    return fake_mod


# ─── /api/health ──────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, client):
        with patch.object(app_mod, "get_health", return_value={
            "status": "ok", "indice_ok": True,
            "chunks_indexados": 34562, "libros": ["Harrison"],
            "hf_activo": False, "modo": "RAG Template",
            "tools_disponibles": [],
        }):
            r = client.get("/api/health")
        assert r.status_code == 200

    def test_ok_status_has_required_keys(self, client):
        with patch.object(app_mod, "get_health", return_value={
            "status": "ok", "indice_ok": True,
            "chunks_indexados": 34562, "libros": [],
            "hf_activo": False, "modo": "RAG", "tools_disponibles": [],
        }):
            r = client.get("/api/health")
        data = r.get_json()
        assert data["status"] == "ok"
        assert data["chunks_indexados"] == 34562

    def test_degraded_when_index_missing(self, client):
        with patch.object(app_mod, "get_health", return_value={
            "status": "degraded", "indice_ok": False,
            "chunks_indexados": 0, "libros": [],
        }):
            r = client.get("/api/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "degraded"


# ─── /api/query ───────────────────────────────────────────────────────────────

class TestQueryEndpoint:
    def test_empty_body_400(self, client):
        r = client.post("/api/query", json={})
        assert r.status_code == 400

    def test_message_too_short_400(self, client):
        r = client.post("/api/query", json={"message": "ok"})
        assert r.status_code == 400

    def test_missing_index_returns_503(self, client):
        with patch.object(app_mod, "run", side_effect=FileNotFoundError("no index")):
            r = client.post("/api/query", json={"message": "tengo fiebre y dolor de cabeza"})
        assert r.status_code == 503
        data = r.get_json()
        assert "error" in data
        assert "ingest" in data["error"].lower()

    def test_successful_query_returns_success_true(self, client):
        with patch.object(app_mod, "run", return_value=_fake_run_result()):
            r = client.post("/api/query", json={"message": "tengo fiebre y dolor muscular"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert data["gravedad"] == "leve"
        assert "respuesta" in data
        assert "disclaimer" in data

    def test_response_has_all_ui_fields(self, client):
        with patch.object(app_mod, "run", return_value=_fake_run_result()):
            r = client.post("/api/query", json={"message": "me duele el pecho y el brazo"})
        data = r.get_json()
        for field in ["gravedad_label", "gravedad_color", "gravedad_icon",
                      "condicion_principal", "recomendacion", "confianza",
                      "fuentes", "trajectory", "tools_used", "modo"]:
            assert field in data, f"Campo faltante: {field}"


# ─── /api/stream ──────────────────────────────────────────────────────────────

class TestStreamEndpoint:
    def test_empty_body_400(self, client):
        r = client.post("/api/stream", json={})
        assert r.status_code == 400

    def test_message_too_short_400(self, client):
        r = client.post("/api/stream", json={"message": "ok"})
        assert r.status_code == 400

    def test_non_medical_query_400(self, client):
        r = client.post("/api/stream", json={"message": "cual es la receta del arroz con pollo"})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_sse_content_type_on_valid_query(self, client, monkeypatch):
        """Sin HF_TOKEN, devuelve text/event-stream con un evento done."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with patch.object(app_mod, "run", return_value=_fake_run_result()):
            r = client.post("/api/stream", json={"message": "tengo fiebre y dolor de garganta"})
        assert r.status_code == 200
        assert "text/event-stream" in r.content_type

    def test_sse_body_contains_done_event(self, client, monkeypatch):
        """El cuerpo SSE debe tener exactamente un evento done."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with patch.object(app_mod, "run", return_value=_fake_run_result()):
            r = client.post("/api/stream", json={"message": "tengo fiebre y dolor de garganta"})
        body = r.data.decode()
        events = [
            json.loads(line[5:].strip())
            for line in body.split("\n\n")
            if line.startswith("data:")
        ]
        assert len(events) == 1
        assert events[0]["type"] == "done"

    def test_missing_index_emits_sse_error(self, client, monkeypatch):
        """Si el indice falta, el SSE debe emitir un evento de error (no 5xx)."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with patch.object(app_mod, "run", side_effect=FileNotFoundError("no index")):
            r = client.post("/api/stream", json={"message": "tengo fiebre y escalofrios"})
        assert r.status_code == 200
        body = r.data.decode()
        events = [
            json.loads(line[5:].strip())
            for line in body.split("\n\n")
            if line.startswith("data:")
        ]
        assert any(e["type"] == "error" for e in events)


# ─── /api/export/pdf ──────────────────────────────────────────────────────────

class TestExportPdfEndpoint:
    def test_empty_body_400(self, client):
        r = client.post("/api/export/pdf", json={})
        assert r.status_code == 400

    def test_missing_respuesta_400(self, client):
        r = client.post("/api/export/pdf", json={"gravedad": "leve"})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_returns_pdf_bytes(self, client):
        payload = {
            "respuesta": "El paciente presenta fiebre viral.",
            "gravedad": "leve",
            "gravedad_label": "LEVE",
            "condicion_principal": "Fiebre viral",
            "recomendacion": "Reposo y liquidos.",
            "fuentes": ["Harrison Principios"],
            "modo": "RAG Template",
            "query": "tengo fiebre",
        }
        with patch.dict("sys.modules", {"weasyprint": _fake_weasyprint_module()}):
            r = client.post("/api/export/pdf", json=payload)
        assert r.status_code == 200
        assert r.content_type == "application/pdf"
        assert r.data.startswith(b"%PDF")

    def test_pdf_content_disposition_is_attachment(self, client):
        payload = {
            "respuesta": "Diagnostico de prueba.",
            "gravedad": "moderada",
            "gravedad_label": "MODERADA",
            "condicion_principal": "Test",
            "recomendacion": "Consultar medico.",
        }
        with patch.dict("sys.modules", {"weasyprint": _fake_weasyprint_module()}):
            r = client.post("/api/export/pdf", json=payload)
        assert r.status_code == 200
        assert "attachment" in r.headers.get("Content-Disposition", "")
        assert ".pdf" in r.headers.get("Content-Disposition", "")

    def test_fpdf_error_returns_500(self, client):
        payload = {"respuesta": "Diagnostico.", "gravedad": "leve"}
        with patch("app._build_pdf_bytes", side_effect=Exception("fpdf error")):
            r = client.post("/api/export/pdf", json=payload)
        assert r.status_code == 500
        assert "error" in r.get_json()
