"""
MEDI-IA Agent — Punto de entrada principal.
Orquesta entre el agente ReAct (HuggingFace) y el pipeline RAG de respaldo.
"""

import os
from dotenv import load_dotenv
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")

GRAVITY_LEVELS = {
    "leve":       {"label": "LEVE",       "color": "#22c55e", "icon": "🟢", "description": "No requiere atencion urgente."},
    "moderada":   {"label": "MODERADA",   "color": "#f59e0b", "icon": "🟡", "description": "Consulta medica en 24-48 horas."},
    "grave":      {"label": "GRAVE",      "color": "#ef4444", "icon": "🔴", "description": "Atencion medica pronto."},
    "emergencia": {"label": "EMERGENCIA", "color": "#8b5cf6", "icon": "🚨", "description": "Llama al 123 o ve a urgencias AHORA."},
}


def run(sintomas: str, session_id: str = "default") -> dict:
    """
    Entrada principal del agente.
    Con HF_TOKEN: usa agente ReAct con Qwen2.5-7B + tools.
    Sin HF_TOKEN: usa pipeline RAG con template.
    """
    from src.guardrails import is_medical_query, refusal_result
    if not is_medical_query(sintomas):
        return refusal_result()

    if HF_TOKEN:
        return _run_react_agent(sintomas, session_id)
    return _run_rag_fallback(sintomas)


def _run_react_agent(sintomas: str, session_id: str) -> dict:
    from src.agent_loop import run_react
    result = run_react(session_id, sintomas)
    nivel = GRAVITY_LEVELS.get(result["gravedad"], GRAVITY_LEVELS["moderada"])
    result["gravedad_info"] = nivel
    result["condicion_principal"] = _extract_condition(result["respuesta"])
    result["recomendacion"] = _extract_recommendation(result["respuesta"])
    result["score_confianza"] = min(95, 60 + result["iteraciones"] * 10)
    return result


def _run_rag_fallback(sintomas: str) -> dict:
    """Pipeline RAG sin LLM — usado cuando no hay HF_TOKEN."""
    from src.rag.retriever import retrieve
    from src.rag.reranker import rerank
    from src.rag.section_mapping import enrich_chunks
    from src.rag.semantic_fallback import needs_fallback, fallback_response

    candidates = retrieve(sintomas, top_k=10)
    ranked = rerank(sintomas, candidates, top_k=5)
    enriched = enrich_chunks(ranked)

    if needs_fallback(enriched):
        r = fallback_response(sintomas)
        r["gravedad_info"] = GRAVITY_LEVELS["moderada"]
        r["condicion_principal"] = "Informacion insuficiente"
        r["recomendacion"] = "Consultar con un profesional de la salud."
        r["score_confianza"] = 0
        r["modo"] = "RAG Template (sin HF_TOKEN)"
        return r

    top = enriched[0]
    nivel = GRAVITY_LEVELS["moderada"]
    respuesta = (
        f"Basandome en los libros medicos, los fragmentos mas relevantes para "
        f"({sintomas}) provienen de **{top['book']}** ({top.get('seccion','?')}, p.{top['page']}):\n\n"
        f"{top['text']}\n\nEsto no reemplaza la consulta medica profesional."
    )
    fuentes = list({c["book"] for c in enriched})

    return {
        "respuesta": respuesta,
        "condicion_principal": top["book"],
        "gravedad": "moderada",
        "gravedad_info": nivel,
        "recomendacion": f"Informacion de: {', '.join(fuentes)}. Consultar medico.",
        "condiciones_relacionadas": [],
        "urgencia": "moderada",
        "score_confianza": round(top.get("score", 0) * 100, 1),
        "fuentes": fuentes,
        "modo": "RAG Template (sin HF_TOKEN)",
        "trajectory": [],
        "tools_used": [],
    }


def _extract_condition(text: str) -> str:
    import re
    match = re.search(r"Condicion principal sugerida[:\*]*\s*\*?\*?([^\n\*]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else "Ver respuesta completa"


def _extract_recommendation(text: str) -> str:
    import re
    match = re.search(r"Recomendacion[:\*]*\s*\*?\*?([^\n]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else "Consultar con un medico."


def get_health() -> dict:
    from src.rag.retriever import get_index_stats
    stats = get_index_stats()
    return {
        "status": "ok",
        "modo": "ReAct Agent (Qwen2.5-7B via HuggingFace)" if HF_TOKEN else "RAG Template",
        "hf_activo": bool(HF_TOKEN),
        "chunks_indexados": stats["total_chunks"],
        "libros": stats["libros"],
        "tools_disponibles": ["search_symptoms", "assess_urgency", "get_drug_info", "get_section"],
    }
