"""
Reranker con cross-encoder.
Toma los chunks recuperados por FAISS y los reordena por relevancia real
frente a la query del usuario. Mejora significativamente la precision.
"""

from sentence_transformers import CrossEncoder

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_cross_encoder: CrossEncoder | None = None


def _get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        print(f"[Reranker] Cargando cross-encoder: {CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL, max_length=512)
        print("[Reranker] Cross-encoder listo.")
    return _cross_encoder


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    Reordena chunks usando cross-encoder y devuelve los top_k mejores.
    El cross-encoder evalua (query, chunk) como par — mucho mas preciso
    que la similitud coseno del retriever.
    """
    if not chunks:
        return []

    encoder = _get_cross_encoder()
    pairs = [(query, c["text"]) for c in chunks]
    scores = encoder.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]
