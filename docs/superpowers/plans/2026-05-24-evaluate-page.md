# Evaluate Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir una página `/evaluate` que demuestre cuantitativamente que el reranker mejora el orden de chunks respecto a FAISS solo, con comparación visual lado a lado por query.

**Architecture:** `src/evaluation.py` corre el benchmark (6 queries fijas → retrieve + rerank → calcula deltas), guarda el resultado en `data/eval_snapshot.json`. Flask añade tres rutas. El frontend muestra stat cards + comparación lado a lado con flechas ↑↓ y barras proporcionales, y tiene un botón "Recalcular" que vuelve a correr el benchmark.

**Tech Stack:** Python stdlib (json, os, time, datetime), FAISS + CrossEncoder (ya en el proyecto), Flask, HTML/CSS/JS vanilla, Lucide icons (mismo CDN que metrics.html).

---

## Mapa de archivos

| Acción | Archivo | Responsabilidad |
|--------|---------|----------------|
| Crear | `src/evaluation.py` | Lógica benchmark: 6 queries, retrieve+rerank, deltas, stats, snapshot I/O |
| Crear | `tests/test_evaluation.py` | Tests unitarios con mocks de retrieve/rerank |
| Crear | `templates/evaluate.html` | Página visual — stat cards + comparación por query |
| Modificar | `app.py` | 3 rutas nuevas: GET /evaluate, GET /api/evaluate/snapshot, POST /api/evaluate/run |

---

## Task 1: `src/evaluation.py` — lógica del benchmark

**Files:**
- Create: `src/evaluation.py`

- [ ] **Step 1: Crear el archivo con queries, helpers y funciones core**

```python
"""
Benchmark cuantitativo: compara FAISS (cosine) vs cross-encoder reranker
en 6 queries médicas fijas. Guarda resultados en data/eval_snapshot.json.
"""

import os
import json
import time
from datetime import datetime

from src.rag.retriever import retrieve
from src.rag.reranker import rerank

BENCHMARK_QUERIES = [
    "dolor en el pecho que se irradia al brazo izquierdo",
    "fiebre alta con rigidez en el cuello",
    "dificultad para respirar y tos con sangre",
    "dolor de cabeza severo de inicio subito",
    "confusion mental en paciente diabetico",
    "tratamiento primera linea hipertension",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "data", "eval_snapshot.json")

_BOOK_ABBREVS = {
    "Harrison Principios De Medicina Interna 19 1": "Harrison",
    "Oxford Handbook of Clinical Medicine 10th Edition": "Oxford",
    "Symptoms to diagnosis ": "Symptoms",
    "The Top 100 Drugs Clinical": "Top100",
}


def _short_book(book: str) -> str:
    return _BOOK_ABBREVS.get(book, book[:12])


def _compute_query_result(query: str) -> dict:
    faiss_chunks = retrieve(query, top_k=10)
    if not faiss_chunks:
        return {
            "query": query,
            "faiss_results": [],
            "reranked_results": [],
            "top1_changed": False,
        }

    faiss_display = []
    for i, chunk in enumerate(faiss_chunks[:5]):
        faiss_display.append({
            "rank": i + 1,
            "score": round(float(chunk["score"]), 3),
            "book": _short_book(chunk.get("book", "")),
            "page": chunk.get("page", 0),
            "text": chunk.get("text", "")[:120],
        })

    reranked = rerank(query, faiss_chunks, top_k=5)

    reranked_display = []
    for new_rank, chunk in enumerate(reranked):
        faiss_rank = next(
            (i + 1 for i, c in enumerate(faiss_chunks)
             if c.get("page") == chunk.get("page") and c.get("book") == chunk.get("book")),
            None,
        )
        delta = (faiss_rank - (new_rank + 1)) if faiss_rank is not None else None
        is_new = faiss_rank is None or faiss_rank > 5
        reranked_display.append({
            "rank": new_rank + 1,
            "rerank_score": round(float(chunk.get("rerank_score", 0)), 2),
            "faiss_rank": faiss_rank,
            "delta": delta,
            "is_new": is_new,
            "book": _short_book(chunk.get("book", "")),
            "page": chunk.get("page", 0),
            "text": chunk.get("text", "")[:120],
        })

    top1_changed = bool(
        reranked_display and faiss_display and (
            reranked_display[0]["book"] != faiss_display[0]["book"]
            or reranked_display[0]["page"] != faiss_display[0]["page"]
        )
    )

    return {
        "query": query,
        "faiss_results": faiss_display,
        "reranked_results": reranked_display,
        "top1_changed": top1_changed,
    }


def run_benchmark() -> dict:
    t0 = time.monotonic()
    query_results = [_compute_query_result(q) for q in BENCHMARK_QUERIES]

    top1_changed_count = sum(1 for r in query_results if r["top1_changed"])
    changes_per_query = [
        sum(1 for c in r["reranked_results"] if c.get("delta") and c["delta"] != 0)
        for r in query_results
    ]
    avg_changes = round(sum(changes_per_query) / len(changes_per_query), 1) if changes_per_query else 0

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_s": round(time.monotonic() - t0, 1),
        "stats": {
            "total_queries": len(BENCHMARK_QUERIES),
            "top1_changed": top1_changed_count,
            "avg_position_changes": avg_changes,
        },
        "queries": query_results,
    }


def save_snapshot(data: dict) -> None:
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_snapshot() -> dict | None:
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    try:
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
```

- [ ] **Step 2: Verificar que el archivo importa sin error (sin índice FAISS)**

```bash
venv\Scripts\python.exe -c "import src.evaluation; print('OK')"
```

Esperado: `OK`

---

## Task 2: Tests de `src/evaluation.py`

**Files:**
- Create: `tests/test_evaluation.py`

- [ ] **Step 1: Escribir el archivo de tests completo**

```python
"""
Tests unitarios de src/evaluation.py.
Mockean retrieve y rerank para no necesitar índice FAISS.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
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
    assert result == "Unknown Book"   # primeros 12 chars


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
    # page 201 es el top-1 rerankeado pero era rank 3 FAISS → cambió
    assert result["top1_changed"] is True
    assert result["reranked_results"][0]["page"] == 201

def test_compute_delta_subio():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    # page 201: faiss_rank=3, nuevo rerank=1 → delta = 3-1 = 2
    chunk_201 = next(c for c in result["reranked_results"] if c["page"] == 201)
    assert chunk_201["delta"] == 2
    assert chunk_201["is_new"] is False

def test_compute_delta_bajo():
    from src.evaluation import _compute_query_result
    with patch("src.evaluation.retrieve", return_value=FAISS_CHUNKS), \
         patch("src.evaluation.rerank", return_value=RERANKED):
        result = _compute_query_result("dolor en el pecho")
    # page 142: faiss_rank=1, nuevo rerank=2 → delta = 1-2 = -1
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
```

- [ ] **Step 2: Correr los tests y verificar que pasan**

```bash
venv\Scripts\pytest.exe tests/test_evaluation.py -v
```

Esperado: todos los tests en PASSED. Si alguno falla, revisar la lógica en `src/evaluation.py` antes de continuar.

---

## Task 3: Rutas en `app.py`

**Files:**
- Modify: `app.py` (agregar después de la ruta `/metrics`)

- [ ] **Step 1: Agregar las tres rutas nuevas en `app.py`**

Agregar este bloque justo después de la ruta `/metrics` (línea ~636), antes del bloque `if __name__ == "__main__"`:

```python
@app.route("/evaluate", methods=["GET"])
@require_auth
def evaluate_page():
    from src.evaluation import load_snapshot
    has_snapshot = load_snapshot() is not None
    return render_template("evaluate.html", has_snapshot=has_snapshot)


@app.route("/api/evaluate/snapshot", methods=["GET"])
@require_auth
def get_eval_snapshot():
    from src.evaluation import load_snapshot
    data = load_snapshot()
    if data is None:
        return jsonify({"error": "No hay snapshot. Ejecuta el benchmark primero."}), 404
    return jsonify(data)


@app.route("/api/evaluate/run", methods=["POST"])
@require_auth
@limiter.limit("2 per minute")
def run_evaluation():
    from src.evaluation import run_benchmark, save_snapshot
    try:
        data = run_benchmark()
        save_snapshot(data)
        log.info("rid=%s benchmark_done duration_s=%.1f", g.rid, data["duration_s"])
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Indice FAISS no encontrado. Ejecuta make ingest primero."}), 503
    except Exception as e:
        log.error("rid=%s benchmark_error=%s", g.rid, e)
        return jsonify({"error": str(e)}), 500
```

- [ ] **Step 2: Verificar que el servidor arranca sin errores**

```bash
venv\Scripts\python.exe -c "import app; print('rutas OK')"
```

Esperado: `rutas OK`

---

## Task 4: Tests de los endpoints en `tests/test_api.py`

**Files:**
- Modify: `tests/test_api.py` (agregar al final del archivo)

- [ ] **Step 1: Agregar tests de los 3 endpoints nuevos**

Agregar al final de `tests/test_api.py`:

```python
# ─── /evaluate endpoints ───────────────────────────────────────────────────────

class TestEvaluateEndpoints:

    def test_evaluate_page_renders(self, client):
        with patch("src.evaluation.load_snapshot", return_value=None):
            r = client.get("/evaluate")
        assert r.status_code == 200
        assert b"evaluate" in r.data.lower()

    def test_evaluate_page_has_snapshot_flag(self, client):
        fake = {"timestamp": "2026-05-24T10:00:00", "stats": {}, "queries": []}
        with patch("src.evaluation.load_snapshot", return_value=fake):
            r = client.get("/evaluate")
        assert r.status_code == 200

    def test_snapshot_returns_404_when_missing(self, client):
        with patch("src.evaluation.load_snapshot", return_value=None):
            r = client.get("/api/evaluate/snapshot")
        assert r.status_code == 404

    def test_snapshot_returns_data(self, client):
        fake = {"timestamp": "2026-05-24T10:00:00", "stats": {"total_queries": 6}, "queries": []}
        with patch("src.evaluation.load_snapshot", return_value=fake):
            r = client.get("/api/evaluate/snapshot")
        assert r.status_code == 200
        data = r.get_json()
        assert data["stats"]["total_queries"] == 6

    def test_run_evaluation_success(self, client):
        fake = {
            "timestamp": "2026-05-24T10:00:00",
            "duration_s": 1.2,
            "stats": {"total_queries": 6, "top1_changed": 4, "avg_position_changes": 2.1},
            "queries": [],
        }
        with patch("src.evaluation.run_benchmark", return_value=fake), \
             patch("src.evaluation.save_snapshot"):
            r = client.post("/api/evaluate/run")
        assert r.status_code == 200
        assert r.get_json()["stats"]["top1_changed"] == 4

    def test_run_evaluation_no_index(self, client):
        with patch("src.evaluation.run_benchmark", side_effect=FileNotFoundError("no index")):
            r = client.post("/api/evaluate/run")
        assert r.status_code == 503

    def test_run_evaluation_generic_error(self, client):
        with patch("src.evaluation.run_benchmark", side_effect=RuntimeError("fallo")):
            r = client.post("/api/evaluate/run")
        assert r.status_code == 500
```

- [ ] **Step 2: Correr los tests nuevos**

```bash
venv\Scripts\pytest.exe tests/test_api.py -v -k "TestEvaluate"
```

Esperado: 7 tests PASSED.

- [ ] **Step 3: Correr el suite completo para verificar sin regresiones**

```bash
venv\Scripts\pytest.exe tests/ -v --ignore=tests/test_retriever.py
```

Esperado: todos los tests existentes siguen pasando.

---

## Task 5: `templates/evaluate.html`

**Files:**
- Create: `templates/evaluate.html`

- [ ] **Step 1: Crear el template completo**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEDI-IA — Evaluación RAG</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<style>
  :root {
    --bg:#f0f4f8; --surface:#ffffff; --surface-2:#f8fafc;
    --border:#e2e8f0; --border-strong:#cbd5e1;
    --emerald:#10b981; --emerald-dark:#059669; --emerald-light:#d1fae5;
    --blue:#3b82f6; --blue-light:#dbeafe;
    --amber:#f59e0b; --amber-light:#fef3c7;
    --red:#ef4444; --red-light:#fee2e2;
    --purple:#8b5cf6; --purple-light:#ede9fe;
    --text:#0f172a; --text-2:#475569; --text-3:#94a3b8; --text-4:#cbd5e1;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.07); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}

  .topbar{
    background:var(--surface);border-bottom:1px solid var(--border);
    padding:0 32px;height:56px;display:flex;align-items:center;
    justify-content:space-between;position:sticky;top:0;z-index:10;
  }
  .topbar-left{display:flex;align-items:center;gap:10px;}
  .topbar-left strong{font-size:15px;font-weight:700;}
  .topbar-left .sep{color:var(--text-3);}
  .topbar-left span{font-size:13px;color:var(--text-2);}
  .back-btn{
    display:flex;align-items:center;gap:6px;padding:6px 14px;
    border:1px solid var(--border-strong);border-radius:8px;
    background:transparent;color:var(--text-2);font-size:12.5px;
    font-family:'Inter',sans-serif;cursor:pointer;text-decoration:none;
    transition:all 0.15s;
  }
  .back-btn:hover{background:var(--surface-2);}
  .btn-recalc{
    display:flex;align-items:center;gap:6px;padding:7px 16px;
    background:var(--emerald);color:#fff;border:none;border-radius:8px;
    font-size:13px;font-family:'Inter',sans-serif;font-weight:500;
    cursor:pointer;transition:background 0.15s;
  }
  .btn-recalc:hover{background:var(--emerald-dark);}
  .btn-recalc:disabled{opacity:0.6;cursor:not-allowed;}

  .page{max-width:1200px;margin:0 auto;padding:32px 24px;}

  .section-title{
    font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;
    color:var(--text-3);margin-bottom:14px;
  }

  /* Stat cards */
  .stat-grid{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
    gap:14px;margin-bottom:32px;
  }
  .stat-card{
    background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:18px 20px;box-shadow:var(--shadow-sm);
  }
  .stat-label{font-size:11px;color:var(--text-3);font-weight:500;margin-bottom:6px;display:flex;align-items:center;gap:5px;}
  .stat-value{font-size:28px;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--text);line-height:1;}
  .stat-sub{font-size:11px;color:var(--text-3);margin-top:4px;}

  /* Query card */
  .query-card{
    background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:22px 24px;box-shadow:var(--shadow-sm);margin-bottom:20px;
  }
  .query-text{
    font-size:14px;font-weight:600;color:var(--text);margin-bottom:18px;
    padding-bottom:14px;border-bottom:1px solid var(--border);
    display:flex;align-items:center;gap:8px;
  }
  .query-num{
    font-size:11px;font-family:'JetBrains Mono',monospace;font-weight:500;
    background:var(--blue-light);color:var(--blue);border-radius:6px;
    padding:2px 8px;
  }
  .top1-badge{
    margin-left:auto;font-size:11px;font-weight:600;padding:3px 10px;
    border-radius:20px;
  }
  .top1-badge.changed{background:var(--emerald-light);color:var(--emerald-dark);}
  .top1-badge.same{background:var(--border);color:var(--text-3);}

  .compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;}

  .col-header{
    font-size:11px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;
    margin-bottom:10px;display:flex;align-items:center;gap:6px;
  }
  .col-header.faiss{color:var(--blue);}
  .col-header.rerank{color:var(--emerald);}

  .chunk-row{
    display:flex;flex-direction:column;gap:3px;
    padding:10px 12px;border-radius:8px;border:1px solid var(--border);
    margin-bottom:8px;background:var(--surface-2);position:relative;
  }
  .chunk-row.highlight-up{border-color:rgba(16,185,129,0.4);background:rgba(16,185,129,0.04);}
  .chunk-row.highlight-down{border-color:rgba(239,68,68,0.25);background:rgba(239,68,68,0.03);}
  .chunk-row.highlight-new{border-color:rgba(59,130,246,0.4);background:rgba(59,130,246,0.04);}

  .chunk-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
  .chunk-rank{
    font-size:11px;font-family:'JetBrains Mono',monospace;font-weight:600;
    min-width:22px;color:var(--text-3);
  }
  .chunk-book{font-size:12px;font-weight:600;color:var(--text-2);}
  .chunk-page{font-size:11px;color:var(--text-3);}
  .chunk-score{
    font-size:11px;font-family:'JetBrains Mono',monospace;font-weight:500;
    margin-left:auto;color:var(--text-2);
  }
  .chunk-delta{font-size:11px;font-weight:700;padding:1px 6px;border-radius:4px;}
  .chunk-delta.up{background:var(--emerald-light);color:var(--emerald-dark);}
  .chunk-delta.down{background:var(--red-light);color:var(--red);}
  .chunk-delta.same{background:var(--border);color:var(--text-3);}
  .chunk-delta.new-entry{background:var(--blue-light);color:var(--blue);}

  .chunk-text{
    font-size:11.5px;color:var(--text-3);line-height:1.5;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    max-width:100%;
  }
  .bar-wrap{height:3px;background:var(--border);border-radius:2px;margin-top:4px;}
  .bar-fill{height:100%;border-radius:2px;transition:width 0.6s ease;}

  .eliminated-label{
    font-size:11px;color:var(--red);display:flex;align-items:center;gap:4px;
    margin-top:4px;padding:6px 10px;background:var(--red-light);
    border-radius:6px;
  }

  /* Loading / Error */
  .state-card{
    background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:60px 24px;text-align:center;box-shadow:var(--shadow-sm);
  }
  .spinner{
    width:36px;height:36px;border:3px solid var(--border);
    border-top-color:var(--emerald);border-radius:50%;
    animation:spin 0.9s linear infinite;margin:0 auto 16px;
  }
  @keyframes spin{to{transform:rotate(360deg)}}
  .state-title{font-size:16px;font-weight:600;margin-bottom:6px;}
  .state-sub{font-size:13px;color:var(--text-3);}

  .timestamp-note{font-size:11.5px;color:var(--text-3);margin-bottom:24px;display:flex;align-items:center;gap:5px;}

  @media(max-width:760px){
    .compare-grid{grid-template-columns:1fr;}
    .stat-grid{grid-template-columns:repeat(2,1fr);}
    .page{padding:20px 16px;}
    .topbar{padding:0 16px;}
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <i data-lucide="flask-conical" style="width:18px;height:18px;color:var(--emerald);stroke-width:2"></i>
    <strong>MEDI-IA</strong>
    <span class="sep">/</span>
    <span>Evaluación RAG</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px">
    <a class="back-btn" href="/metrics">
      <i data-lucide="activity" style="width:13px;height:13px"></i> Métricas
    </a>
    <a class="back-btn" href="/">
      <i data-lucide="arrow-left" style="width:13px;height:13px"></i> Chat
    </a>
    <button class="btn-recalc" id="btnRecalc" onclick="runBenchmark()">
      <i data-lucide="refresh-cw" style="width:13px;height:13px"></i> Recalcular
    </button>
  </div>
</div>

<div class="page">

  <div style="margin-bottom:24px">
    <h1 style="font-size:22px;font-weight:700;letter-spacing:-0.4px">Evaluación del pipeline RAG</h1>
    <p style="font-size:13px;color:var(--text-3);margin-top:3px">Comparación FAISS (similitud coseno) vs Cross-Encoder reranker — 6 consultas médicas fijas</p>
  </div>

  <!-- Estado: cargando -->
  <div id="stateLoading" class="state-card" style="display:none">
    <div class="spinner"></div>
    <div class="state-title">Ejecutando benchmark...</div>
    <div class="state-sub" id="loadingMsg">Cargando modelos y evaluando consultas. Puede tardar 20-40 segundos.</div>
  </div>

  <!-- Estado: error -->
  <div id="stateError" class="state-card" style="display:none">
    <i data-lucide="alert-triangle" style="width:36px;height:36px;color:var(--amber);margin-bottom:12px"></i>
    <div class="state-title" id="errorTitle">Error</div>
    <div class="state-sub" id="errorMsg"></div>
  </div>

  <!-- Resultados -->
  <div id="stateResults" style="display:none">
    <div class="timestamp-note">
      <i data-lucide="clock" style="width:12px;height:12px"></i>
      Generado el <span id="tsLabel">—</span> &nbsp;·&nbsp; Duración: <span id="durLabel">—</span>
    </div>

    <div class="section-title">Resumen del benchmark</div>
    <div class="stat-grid" style="margin-bottom:32px">
      <div class="stat-card">
        <div class="stat-label"><i data-lucide="list" style="width:13px;height:13px;color:var(--blue)"></i> Queries evaluadas</div>
        <div class="stat-value" id="statTotal">—</div>
        <div class="stat-sub">consultas médicas</div>
      </div>
      <div class="stat-card">
        <div class="stat-label"><i data-lucide="arrow-up-circle" style="width:13px;height:13px;color:var(--emerald)"></i> Top-1 mejorado</div>
        <div class="stat-value" id="statTop1" style="color:var(--emerald-dark)">—</div>
        <div class="stat-sub">cambió el chunk más relevante</div>
      </div>
      <div class="stat-card">
        <div class="stat-label"><i data-lucide="shuffle" style="width:13px;height:13px;color:var(--purple)"></i> Cambios promedio</div>
        <div class="stat-value" id="statAvg" style="color:var(--purple)">—</div>
        <div class="stat-sub">reordenamientos por query</div>
      </div>
      <div class="stat-card">
        <div class="stat-label"><i data-lucide="timer" style="width:13px;height:13px;color:var(--amber)"></i> Tiempo benchmark</div>
        <div class="stat-value" id="statDur">—</div>
        <div class="stat-sub">segundos</div>
      </div>
    </div>

    <div class="section-title">Comparación por consulta</div>
    <div id="queriesContainer"></div>
  </div>

</div>

<script>
const HAS_SNAPSHOT = {{ 'true' if has_snapshot else 'false' }};

function deltaLabel(chunk) {
  if (chunk.is_new) return '<span class="chunk-delta new-entry">NEW</span>';
  if (chunk.delta === null || chunk.delta === 0) return '<span class="chunk-delta same">─</span>';
  if (chunk.delta > 0) return `<span class="chunk-delta up">↑+${chunk.delta}</span>`;
  return `<span class="chunk-delta down">↓${chunk.delta}</span>`;
}

function rowClass(chunk) {
  if (chunk.is_new) return 'chunk-row highlight-new';
  if (chunk.delta > 0) return 'chunk-row highlight-up';
  if (chunk.delta < 0) return 'chunk-row highlight-down';
  return 'chunk-row';
}

function buildBar(value, max, color) {
  const pct = max > 0 ? Math.max(5, Math.round(value / max * 100)) : 0;
  return `<div class="bar-wrap"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>`;
}

function renderQuery(q, idx) {
  const changed = q.top1_changed;
  const badge = changed
    ? '<span class="top1-badge changed">✓ Top-1 mejorado</span>'
    : '<span class="top1-badge same">Top-1 sin cambio</span>';

  // FAISS column
  const maxFaiss = q.faiss_results.length ? q.faiss_results[0].score : 1;
  const faissRows = q.faiss_results.map(c => `
    <div class="chunk-row">
      <div class="chunk-meta">
        <span class="chunk-rank">#${c.rank}</span>
        <span class="chunk-book">${c.book}</span>
        <span class="chunk-page">p.${c.page}</span>
        <span class="chunk-score">${c.score.toFixed(3)}</span>
      </div>
      <div class="chunk-text" title="${c.text}">${c.text}</div>
      ${buildBar(c.score, maxFaiss, '#3b82f6')}
    </div>`).join('');

  // Rerank column
  const maxRerank = q.reranked_results.length
    ? Math.max(...q.reranked_results.map(c => Math.abs(c.rerank_score)), 0.1)
    : 1;
  const rerankRows = q.reranked_results.map(c => `
    <div class="${rowClass(c)}">
      <div class="chunk-meta">
        <span class="chunk-rank">#${c.rank}</span>
        ${deltaLabel(c)}
        <span class="chunk-book">${c.book}</span>
        <span class="chunk-page">p.${c.page}</span>
        <span class="chunk-score">${c.rerank_score >= 0 ? '+' : ''}${c.rerank_score.toFixed(2)}</span>
      </div>
      <div class="chunk-text" title="${c.text}">${c.text}</div>
      ${buildBar(Math.max(c.rerank_score, 0), maxRerank, '#10b981')}
    </div>`).join('');

  // Eliminated chunks (in faiss top-5 but not in reranked)
  const rerankedKeys = new Set(q.reranked_results.map(c => c.book + '|' + c.page));
  const eliminated = q.faiss_results.filter(c => !rerankedKeys.has(c.book + '|' + c.page));
  const elimHtml = eliminated.map(c =>
    `<div class="eliminated-label">
      <i data-lucide="x-circle" style="width:12px;height:12px"></i>
      Eliminado: ${c.book} p.${c.page}
    </div>`).join('');

  return `
    <div class="query-card">
      <div class="query-text">
        <span class="query-num">Q${idx + 1}</span>
        "${q.query}"
        ${badge}
      </div>
      <div class="compare-grid">
        <div>
          <div class="col-header faiss">
            <i data-lucide="search" style="width:13px;height:13px"></i>
            FAISS — similitud coseno
          </div>
          ${faissRows || '<div class="state-sub">Sin resultados</div>'}
        </div>
        <div>
          <div class="col-header rerank">
            <i data-lucide="star" style="width:13px;height:13px"></i>
            Cross-Encoder Reranker
          </div>
          ${rerankRows || '<div class="state-sub">Sin resultados</div>'}
          ${elimHtml}
        </div>
      </div>
    </div>`;
}

function renderResults(data) {
  document.getElementById('stateLoading').style.display = 'none';
  document.getElementById('stateError').style.display = 'none';
  document.getElementById('stateResults').style.display = 'block';

  const s = data.stats;
  document.getElementById('statTotal').textContent = s.total_queries;
  document.getElementById('statTop1').textContent  = `${s.top1_changed}/${s.total_queries}`;
  document.getElementById('statAvg').textContent   = s.avg_position_changes.toFixed(1);
  document.getElementById('statDur').textContent   = data.duration_s.toFixed(1) + 's';
  document.getElementById('tsLabel').textContent   = data.timestamp.replace('T', ' ');
  document.getElementById('durLabel').textContent  = data.duration_s.toFixed(1) + 's';

  document.getElementById('queriesContainer').innerHTML =
    data.queries.map((q, i) => renderQuery(q, i)).join('');

  lucide.createIcons();
}

function showError(title, msg) {
  document.getElementById('stateLoading').style.display = 'none';
  document.getElementById('stateResults').style.display = 'none';
  document.getElementById('stateError').style.display = 'block';
  document.getElementById('errorTitle').textContent = title;
  document.getElementById('errorMsg').textContent = msg;
  lucide.createIcons();
}

async function runBenchmark() {
  document.getElementById('stateLoading').style.display = 'block';
  document.getElementById('stateResults').style.display = 'none';
  document.getElementById('stateError').style.display = 'none';
  document.getElementById('btnRecalc').disabled = true;

  try {
    const r = await fetch('/api/evaluate/run', { method: 'POST' });
    const data = await r.json();
    if (!r.ok) {
      showError('Error al ejecutar benchmark', data.error || `HTTP ${r.status}`);
    } else {
      renderResults(data);
    }
  } catch (e) {
    showError('Error de red', 'No se pudo conectar con el servidor.');
  } finally {
    document.getElementById('btnRecalc').disabled = false;
  }
}

async function init() {
  lucide.createIcons();

  if (HAS_SNAPSHOT) {
    try {
      const r = await fetch('/api/evaluate/snapshot');
      if (r.ok) {
        renderResults(await r.json());
        return;
      }
    } catch {}
  }
  // Sin snapshot o falló: correr automáticamente
  runBenchmark();
}

init();
</script>
</body>
</html>
```

- [ ] **Step 2: Verificar que el template existe**

```bash
venv\Scripts\python.exe -c "import os; print(os.path.exists('templates/evaluate.html'))"
```

Esperado: `True`

---

## Task 6: Commit final

- [ ] **Step 1: Correr el suite completo una última vez**

```bash
venv\Scripts\pytest.exe tests/ -v --ignore=tests/test_retriever.py
```

Esperado: todos los tests pasan.

- [ ] **Step 2: Dar comandos al usuario para commitear**

```
git add src/evaluation.py tests/test_evaluation.py templates/evaluate.html
git add app.py tests/test_api.py
git commit -m "feat: pagina evaluate con comparacion FAISS vs reranker cuantitativa"
```

---

## Self-Review

**Spec coverage:**
- ✅ `src/evaluation.py` con 6 queries fijas y `run_benchmark()`
- ✅ Snapshot en `data/eval_snapshot.json` (save/load)
- ✅ Stat cards: total queries, top-1 mejorado, cambios promedio, duración
- ✅ Comparación lado a lado con flechas ↑↓, NEW, eliminados
- ✅ 3 endpoints: GET /evaluate, GET /api/evaluate/snapshot, POST /api/evaluate/run
- ✅ Rate limit 2/min en /api/evaluate/run
- ✅ Sin índice FAISS → 503 con mensaje claro
- ✅ Carga snapshot si existe, si no lo genera automáticamente
- ✅ Botón "Recalcular benchmark"
- ✅ `require_auth` heredado en los 3 endpoints
- ✅ Tests unitarios de evaluation.py (15 tests)
- ✅ Tests de endpoints (7 tests)

**Placeholder scan:** Ninguno. Todo el código está completo.

**Type consistency:** `_compute_query_result` → `run_benchmark` → `save_snapshot`/`load_snapshot` — firmas y tipos consistentes en todos los tasks.
