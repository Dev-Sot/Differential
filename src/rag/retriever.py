"""
Recupera los chunks mas relevantes del indice FAISS.
"""

import os
import json
import faiss
import numpy as np
from src.rag.embeddings import encode

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index", "books.index")
META_PATH = os.path.join(BASE_DIR, "index", "metadata.json")

MIN_SCORE = 0.25  # umbral minimo para considerar un resultado relevante

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
        print(f"[Retriever] Indice cargado: {_index.ntotal} chunks.")


def retrieve(query: str, top_k: int = 10) -> list[dict]:
    """Devuelve hasta top_k chunks con score >= MIN_SCORE."""
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


def get_index_stats() -> dict:
    _load()
    books = list({m["book"] for m in _metadata})
    return {"total_chunks": _index.ntotal, "libros": books}
