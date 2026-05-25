"""
BM25 keyword-based retrieval complementario al FAISS denso.
Se construye lazy desde el metadata.json existente — no requiere re-ingesta.
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
META_PATH = os.path.join(BASE_DIR, "index", "metadata.json")

_bm25 = None
_corpus: list[dict] | None = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())


def _load():
    global _bm25, _corpus
    if _bm25 is not None:
        return
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        raise ImportError("Instala rank-bm25: pip install rank-bm25")

    if not os.path.exists(META_PATH):
        raise FileNotFoundError("Indice no encontrado. Ejecuta: python ingest.py")

    with open(META_PATH, encoding="utf-8") as f:
        _corpus = json.load(f)

    tokenized = [_tokenize(doc["text"]) for doc in _corpus]
    _bm25 = BM25Okapi(tokenized)
    print(f"[BM25] Indice construido: {len(_corpus)} chunks.")


def retrieve_bm25(query: str, top_k: int = 20) -> list[dict]:
    """Devuelve top_k chunks por coincidencia de keywords (BM25)."""
    _load()
    tokens = _tokenize(query)
    scores = _bm25.get_scores(tokens)

    top_indices = scores.argsort()[-top_k:][::-1]
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            entry = _corpus[idx].copy()
            entry["bm25_score"] = float(scores[idx])
            results.append(entry)
    return results


def reset():
    """Resetea el indice BM25 (necesario tras reload del indice FAISS)."""
    global _bm25, _corpus
    _bm25 = None
    _corpus = None
