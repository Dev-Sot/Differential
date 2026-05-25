"""
Recupera los chunks mas relevantes usando busqueda hibrida:
  FAISS (denso, cosine) + BM25 (keywords) fusionados con Reciprocal Rank Fusion.
"""

import os
import json
import faiss
import numpy as np
from src.rag.embeddings import encode

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index", "books.index")
META_PATH = os.path.join(BASE_DIR, "index", "metadata.json")

MIN_SCORE = 0.20  # umbral minimo cosine para FAISS

_index: faiss.Index | None = None
_metadata: list[dict] | None = None


def _load():
    global _index, _metadata
    if _index is None:
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(
                "Indice FAISS no encontrado. Ejecuta: python ingest.py"
            )
        _index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
        # Validar que el indice es compatible con el modelo de embeddings actual
        test_vec = encode(["test"])
        if _index.d != test_vec.shape[1]:
            raise ValueError(
                f"Dimension del indice ({_index.d}) no coincide con el modelo de embeddings "
                f"({test_vec.shape[1]}). Ejecuta: python ingest.py para reconstruir el indice."
            )
        print(f"[Retriever] Indice cargado: {_index.ntotal} chunks (dim={_index.d}).")


def _retrieve_faiss(query: str, top_k: int) -> list[dict]:
    """Busqueda densa con FAISS (cosine similarity via inner product)."""
    _load()
    query_vec = encode([query])
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and float(score) >= MIN_SCORE:
            entry = _metadata[idx].copy()
            entry["score"] = float(score)
            results.append(entry)
    return results


def _rrf(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion: combina multiples rankings en uno solo."""
    scores: dict[tuple, float] = {}
    chunks: dict[tuple, dict] = {}

    for ranking in rankings:
        for rank, chunk in enumerate(ranking):
            key = (chunk.get("book", ""), chunk.get("page", 0))
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in chunks:
                chunks[key] = chunk

    sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [chunks[key] for key in sorted_keys]


def retrieve(query: str, top_k: int = 10) -> list[dict]:
    """
    Busqueda hibrida: FAISS denso + BM25 keywords, fusionados con RRF.
    Si BM25 no esta disponible cae a solo FAISS.
    """
    faiss_results = _retrieve_faiss(query, top_k * 2)

    try:
        from src.rag.bm25_retriever import retrieve_bm25
        bm25_results = retrieve_bm25(query, top_k * 2)
    except Exception:
        bm25_results = []

    if not bm25_results:
        return faiss_results[:top_k]

    merged = _rrf([faiss_results, bm25_results])
    # Preservar el score FAISS en los resultados fusionados para compatibilidad
    faiss_scores = {(c.get("book", ""), c.get("page", 0)): c.get("score", 0.0)
                    for c in faiss_results}
    for chunk in merged:
        key = (chunk.get("book", ""), chunk.get("page", 0))
        if "score" not in chunk:
            chunk["score"] = faiss_scores.get(key, 0.0)

    return merged[:top_k]


def get_index_stats() -> dict:
    _load()
    books = list({m["book"] for m in _metadata})
    return {"total_chunks": _index.ntotal, "libros": books}
