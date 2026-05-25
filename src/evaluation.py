"""
Benchmark cuantitativo: compara FAISS (cosine) vs cross-encoder reranker
en 6 queries medicas fijas. Guarda resultados en data/eval_snapshot.json.
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
    faiss_chunks = retrieve(query, top_k=20)
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
