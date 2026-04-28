"""
Fallback semantico: cuando el retriever no encuentra resultados
con suficiente confianza, responde honestamente en lugar de inventar.
"""

RERANK_THRESHOLD = -9.0  # cross-encoder ms-marco devuelve scores negativos; -9 es umbral conservador
FAISS_THRESHOLD = 0.25   # score minimo del retriever FAISS si no hay reranker


def needs_fallback(chunks: list[dict]) -> bool:
    """Retorna True si los resultados no son suficientemente confiables."""
    if not chunks:
        return True
    top = chunks[0]
    if "rerank_score" in top:
        return top["rerank_score"] < RERANK_THRESHOLD
    return top.get("score", 0) < FAISS_THRESHOLD


def fallback_response(query: str) -> dict:
    """Respuesta honesta cuando no se encontro informacion suficiente."""
    return {
        "respuesta": (
            f'No encontre informacion suficientemente especifica en los libros medicos '
            f'disponibles para los sintomas: "{query}".\n\n'
            "Esto puede deberse a que los sintomas son muy genericos, "
            "o que la condicion requiere evaluacion clinica directa.\n\n"
            "Recomiendo consultar con un medico para una evaluacion adecuada."
        ),
        "condicion_principal": "Informacion insuficiente",
        "gravedad": "moderada",
        "recomendacion": "Consultar con un profesional de la salud para evaluacion presencial.",
        "condiciones_relacionadas": [],
        "urgencia": "moderada",
        "confianza": 0.0,
        "fuentes": [],
        "es_fallback": True,
    }
