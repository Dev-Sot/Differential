"""
Tests unitarios de src/evaluation.py.
Mockean retrieve y rerank para no necesitar indice FAISS.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch

# ── fixtures de datos ──────────────────────────────────────────────────────────

FAISS_CHUNKS = [
    {"book": "Harrison Principios De Medicina Interna 19 1", "page": 142, "text": "Texto A infarto miocardio", "score": 0.84},
    {"book": "Oxford Handbook of Clinical Medicine 10th Edition", "page": 89,  "text": "Texto B angina pectoris",  "score": 0.82},
    {"book": "Harrison Principios De Medicina Interna 19 1", "page": 201, "text": "Texto C IAM STEMI",        "score": 0.80},
    {"book": "Harrison Principios De Medicina Interna 19 1", "page": 98,  "text": "Texto D cardiovascular",   "score": 0.78},
    {"book": "Symptoms to diagnosis ", "page": 44,  "text": "Texto E dolor toracico",   "score": 0.77},
    {"book": "Harrison Principios De Medicina Interna 19 1", "page": 310, "text": "Texto F nuevo capitulo",   "score": 0.70},
]

# Reranker invierte orden: chunk de page 201 (era rank 3) sube a rank 1
# chunk de page 310 (era rank 6, fuera del top-5 FAISS) entra al top-5 rerankeado
RERANKED = [
    {**FAISS_CHUNKS[2], "rerank_score": 7.2},   # page 201, era faiss rank 3 → sube a rerank 1
    {**FAISS_CHUNKS[0], "rerank_score": 5.8},   # page 142, era faiss rank 1 → baja a rerank 2
    {**FAISS_CHUNKS[1], "rerank_score": 4.1},   # page 89,  era faiss rank 2 → baja a rerank 3
    {**FAISS_CHUNKS[4], "rerank_score": 2.3},   # page 44,  era faiss rank 5 → igual
    {**FAISS_CHUNKS[5], "rerank_score": -1.2},  # page 310, era faiss rank 6 → es NEW
]


# ── _short_book ────────────────────────────────────────────────────────────────

def test_short_book_harrison():
    from src.evaluation import _short_book
    assert _short_book("Harrison Principios De Medicina Interna 19 1") == "Harrison"

def test_short_book_oxford():
    from src.evaluation import _short_book
    assert _short_book("Oxford Handbook of Clinical Medicine 10th Edition") == "Oxford"

def test_short_book_symptoms():
    from src.evaluation import _short_book
    assert _short_book("Symptoms to diagnosis ") == "Symptoms"

def test_short_book_top100():
    from src.evaluation import _short_book
    assert _short_book("The Top 100 Drugs Clinical") == "Top100"

def test_short_book_unknown_truncates():
    from src.evaluation import _short_book
    result = _short_book("Unknown Book Name Here")
    assert result == "Unknown Book"  # primeros 12 chars


# ── save_snapshot / load_snapshot ─────────────────────────────────────────────

def test_save_and_load_snapshot(tmp_path, monkeypatch):
    from src import evaluation
    monkeypatch.setattr(evaluation, "SNAPSHOT_PATH", str(tmp_path / "eval.json"))
    data = {"timestamp": "2026-05-24T10:00:00", "stats": {"total_queries": 6}}
    evaluation.save_snapshot(data)
    loaded = evaluation.load_snapshot()
    assert loaded == data

def test_load_snapshot_missing(tmp_path, monkeypatch):
    from src import evaluation
    monkeypatch.setattr(evaluation, "SNAPSHOT_PATH", str(tmp_path / "nonexistent.json"))
    assert evaluation.load_snapshot() is None

def test_load_snapshot_corrupt(tmp_path, monkeypatch):
    from src import evaluation
    path = tmp_path / "eval.json"
    path.write_text("not valid json", encoding="utf-8")
    monkeypatch.setattr(evaluation, "SNAPSHOT_PATH", str(path))
    assert evaluation.load_snapshot() is None

def test_save_snapshot_creates_dir(tmp_path, monkeypatch):
    from src import evaluation
    nested = tmp_path / "new_dir" / "eval.json"
    monkeypatch.setattr(evaluation, "SNAPSHOT_PATH", str(nested))
    evaluation.save_snapshot({"ok": True})
    assert nested.exists()


# ── _compute_query_result ─────────────────────────────────────────────────────

def test_compute_top1_changed():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    assert result["top1_changed"] is True
    assert result["reranked_results"][0]["page"] == 201

def test_compute_delta_subio():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    # page 201: faiss_rank=3, rerank=1 → delta = 3-1 = 2
    chunk_201 = next(c for c in result["reranked_results"] if c["page"] == 201)
    assert chunk_201["delta"] == 2
    assert chunk_201["is_new"] is False

def test_compute_delta_bajo():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    # page 142: faiss_rank=1, rerank=2 → delta = 1-2 = -1
    chunk_142 = next(c for c in result["reranked_results"] if c["page"] == 142)
    assert chunk_142["delta"] == -1

def test_compute_new_chunk():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    # page 310 era faiss rank 6 (>5) → is_new = True
    chunk_310 = next(c for c in result["reranked_results"] if c["page"] == 310)
    assert chunk_310["is_new"] is True

def test_compute_empty_retrieve():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=[]):
        result = _compute_query_result("sin resultados")
    assert result["faiss_results"] == []
    assert result["reranked_results"] == []
    assert result["top1_changed"] is False

def test_compute_faiss_display_top5_only():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    assert len(result["faiss_results"]) == 5

def test_compute_text_truncated_at_120():
    long_chunk = {**FAISS_CHUNKS[0], "text": "A" * 200}
    with patch("src.evaluation.retrieve", return_value=[long_chunk]), \
         patch("src.evaluation.rerank", return_value=[{**long_chunk, "rerank_score": 5.0}]):
        from src.evaluation import _compute_query_result
        result = _compute_query_result("test")
    assert len(result["faiss_results"][0]["text"]) == 120


# ── run_benchmark ─────────────────────────────────────────────────────────────

def test_run_benchmark_structure():
    from src.evaluation import run_benchmark
    mock_result = {
        "query": "test", "faiss_results": [],
        "reranked_results": [], "top1_changed": False,
    }
    with patch("src.evaluation._compute_query_result", return_value=mock_result):
        result = run_benchmark()
    assert "timestamp" in result
    assert "duration_s" in result
    assert "stats" in result
    assert result["stats"]["total_queries"] == 6
    assert len(result["queries"]) == 6

def test_run_benchmark_top1_all_changed():
    from src.evaluation import run_benchmark
    def _mock(query):
        return {"query": query, "faiss_results": [], "reranked_results": [], "top1_changed": True}
    with patch("src.evaluation._compute_query_result", side_effect=_mock):
        result = run_benchmark()
    assert result["stats"]["top1_changed"] == 6

def test_run_benchmark_top1_none_changed():
    from src.evaluation import run_benchmark
    def _mock(query):
        return {"query": query, "faiss_results": [], "reranked_results": [], "top1_changed": False}
    with patch("src.evaluation._compute_query_result", side_effect=_mock):
        result = run_benchmark()
    assert result["stats"]["top1_changed"] == 0

def test_run_benchmark_duration_positive():
    from src.evaluation import run_benchmark
    def _mock(query):
        return {"query": query, "faiss_results": [], "reranked_results": [], "top1_changed": False}
    with patch("src.evaluation._compute_query_result", side_effect=_mock):
        result = run_benchmark()
    assert result["duration_s"] >= 0
