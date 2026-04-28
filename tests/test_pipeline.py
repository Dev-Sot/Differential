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
            for r in results:
                assert r["score"] >= MIN_SCORE
        except FileNotFoundError:
            pytest.skip("Indice FAISS no encontrado.")
