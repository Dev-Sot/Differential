"""
Tests basicos para MEDI-IA.
Ejecutar: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from src.rag.section_mapping import get_section, enrich_chunks
from src.rag.semantic_fallback import needs_fallback, fallback_response
from src.schemas import ConsultaRequest, NivelGravedad


class TestSectionMapping:
    def test_harrison_page_in_range(self):
        section = get_section("Harrison Principios De Medicina Interna 19 1", 55)
        assert section == "Signos y Sintomas Cardinales"

    def test_oxford_page_in_range(self):
        section = get_section("Oxford Handbook of Clinical Medicine 10th Edition", 200)
        assert section == "Cardiovascular medicine"

    def test_unknown_book(self):
        section = get_section("Libro Desconocido", 100)
        assert section == "Seccion general"

    def test_enrich_chunks(self):
        chunks = [{"book": "Oxford Handbook of Clinical Medicine 10th Edition", "page": 250, "text": "test"}]
        enriched = enrich_chunks(chunks)
        assert "seccion" in enriched[0]
        assert enriched[0]["seccion"] == "Chest medicine"


class TestSemanticFallback:
    def test_empty_chunks_needs_fallback(self):
        assert needs_fallback([]) is True

    def test_low_score_needs_fallback(self):
        chunks = [{"text": "test", "rerank_score": -15.0}]
        assert needs_fallback(chunks) is True

    def test_fallback_response_structure(self):
        resp = fallback_response("dolor de espalda")
        assert "respuesta" in resp
        assert resp["gravedad"] == "moderada"
        assert resp["confianza"] == 0.0
        assert resp["es_fallback"] is True


class TestSchemas:
    def test_valid_consulta(self):
        c = ConsultaRequest(message="tengo fiebre y dolor de cabeza")
        assert len(c.message) >= 5

    def test_too_short_consulta(self):
        with pytest.raises(Exception):
            ConsultaRequest(message="ok")

    def test_gravedad_enum(self):
        assert NivelGravedad.emergencia == "emergencia"
        assert NivelGravedad.leve == "leve"


class TestRetriever:
    def test_retrieve_returns_results(self):
        try:
            from src.rag.retriever import retrieve
            results = retrieve("fiebre alta y dolor muscular", top_k=3)
            assert isinstance(results, list)
            if results:
                assert "text" in results[0]
                assert "book" in results[0]
                assert "score" in results[0]
        except FileNotFoundError:
            pytest.skip("Indice FAISS no encontrado. Ejecuta python ingest.py primero.")

    def test_retrieve_score_above_threshold(self):
        try:
            from src.rag.retriever import retrieve, MIN_SCORE
            results = retrieve("infarto de miocardio dolor pecho", top_k=5)
            # En modo híbrido RRF, resultados de BM25 puro pueden tener score=0.0
            # Se verifica que al menos el top resultado tenga score FAISS válido
            faiss_results = [r for r in results if r.get("score", 0) > 0]
            assert len(faiss_results) > 0, "Debe haber al menos un resultado con score FAISS"
            assert faiss_results[0]["score"] >= MIN_SCORE
        except FileNotFoundError:
            pytest.skip("Indice FAISS no encontrado.")


class TestChatStream:
    def test_chat_stream_returns_iterator(self, monkeypatch):
        """chat_stream debe retornar un iterador de strings."""
        from src.llm import chat_stream

        chunks = ["Hola", " mundo", " médico"]

        def fake_completion(**kwargs):
            for text in chunks:
                obj = type("Chunk", (), {
                    "choices": [type("Choice", (), {
                        "delta": type("Delta", (), {"content": text})()
                    })()]
                })()
                yield obj

        monkeypatch.setenv("HF_TOKEN", "fake-token")
        import src.llm as llm_mod
        llm_mod._client = type("FakeClient", (), {
            "chat_completion": lambda self, **kw: fake_completion(**kw)
        })()

        result = list(chat_stream([{"role": "user", "content": "test"}], max_tokens=10))
        assert result == chunks

    def test_chat_stream_skips_none_content(self, monkeypatch):
        """chat_stream debe ignorar chunks con delta.content = None."""
        from src.llm import chat_stream

        def fake_completion(**kwargs):
            # First chunk: None content (role-only chunk, common in HF streams)
            yield type("Chunk", (), {
                "choices": [type("Choice", (), {
                    "delta": type("Delta", (), {"content": None})()
                })()]
            })()
            # Second chunk: real content
            yield type("Chunk", (), {
                "choices": [type("Choice", (), {
                    "delta": type("Delta", (), {"content": "Respuesta"})()
                })()]
            })()

        monkeypatch.setenv("HF_TOKEN", "fake-token")
        import src.llm as llm_mod
        llm_mod._client = type("FakeClient", (), {
            "chat_completion": lambda self, **kw: fake_completion(**kw)
        })()

        result = list(chat_stream([{"role": "user", "content": "test"}], max_tokens=10))
        assert result == ["Respuesta"]  # None chunk was skipped


class TestStreamReact:
    def test_stream_react_yields_event_types(self, monkeypatch):
        """stream_react debe emitir thought, tool_call, observation y done."""
        import src.agent_loop as al

        call_count = [0]
        def fake_chat(messages, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "Thought: voy a buscar\nAction: search_symptoms\nInput: fiebre"
            return "Final Answer: El paciente presenta síndrome gripal."

        def fake_chat_stream(messages, **kwargs):
            yield "El paciente "
            yield "presenta síndrome gripal."

        def fake_execute_tool(name, inp):
            return "Fragmento relevante de Harrison p.301"

        monkeypatch.setattr(al, "chat", fake_chat)
        monkeypatch.setattr("src.agent_loop.chat_stream", fake_chat_stream, raising=False)
        monkeypatch.setattr(al, "execute_tool", fake_execute_tool)
        monkeypatch.setattr(al, "get_history", lambda sid: [{"role": "user", "content": "fiebre"}])
        monkeypatch.setattr(al, "add_turn", lambda *a: None)
        monkeypatch.setattr(al, "set_system", lambda *a: None)

        events = list(al.stream_react("test-session", "tengo fiebre"))
        types = [e["type"] for e in events]

        assert "thought" in types
        assert "tool_call" in types
        assert "observation" in types
        assert "final_start" in types
        assert "token" in types
        assert types[-1] == "done"

    def test_stream_react_done_has_required_fields(self, monkeypatch):
        """El evento done debe tener todos los campos requeridos."""
        import src.agent_loop as al

        monkeypatch.setattr(al, "chat", lambda *a, **kw: "Final Answer: Diagnóstico de prueba.")
        monkeypatch.setattr("src.agent_loop.chat_stream", lambda *a, **kw: iter(["Diagnóstico de prueba."]), raising=False)
        monkeypatch.setattr(al, "get_history", lambda sid: [{"role": "user", "content": "test"}])
        monkeypatch.setattr(al, "add_turn", lambda *a: None)
        monkeypatch.setattr(al, "set_system", lambda *a: None)

        events = list(al.stream_react("test-session", "test"))
        done = next(e for e in events if e["type"] == "done")

        required = ["gravedad", "gravedad_label", "gravedad_color", "gravedad_icon",
                    "condicion_principal", "recomendacion", "respuesta",
                    "trajectory", "fuentes", "confianza", "modo", "tools_used"]
        for field in required:
            assert field in done, f"Campo faltante en done: {field}"
