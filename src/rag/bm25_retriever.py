"""
BM25 keyword-based retrieval complementario al FAISS denso.
Se construye lazy reutilizando la metadata ya cargada por retriever.py —
no requiere re-ingesta ni una segunda copia de metadata.json en memoria.
"""

import re

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
    except ImportError as e:
        raise ImportError("Instala rank-bm25: pip install rank-bm25") from e

    from src.rag import retriever
    retriever._load()
    # Limitar al mismo rango que cubre el indice FAISS: si metadata.json
    # tiene mas chunks que el indice (ver rebuild_index_from_metadata.py),
    # BM25 no debe servir libros que la busqueda densa no puede encontrar —
    # si no, el "8 de 14 libros" documentado en el README seria falso.
    _corpus = retriever._metadata[: retriever._index.ntotal]

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
