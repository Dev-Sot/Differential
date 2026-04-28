"""
Herramientas medicas que el agente ReAct puede llamar.
Cada tool tiene: nombre, descripcion, funcion ejecutable.
"""

import json
from src.rag.retriever import retrieve
from src.rag.reranker import rerank
from src.rag.section_mapping import enrich_chunks


def search_symptoms(query: str) -> str:
    """
    Busca en los libros medicos fragmentos relevantes para los sintomas dados.
    Usa FAISS + reranker para maxima precision.
    """
    candidates = retrieve(query, top_k=10)
    ranked = rerank(query, candidates, top_k=4)
    enriched = enrich_chunks(ranked)

    if not enriched:
        return "No se encontraron fragmentos relevantes para estos sintomas."

    parts = []
    for i, c in enumerate(enriched, 1):
        parts.append(
            f"[Fragmento {i}] {c['book']} | {c.get('seccion','?')} | p.{c['page']}\n{c['text'][:400]}"
        )
    return "\n\n".join(parts)


def assess_urgency(symptoms: str, context: str) -> str:
    """
    Evalua el nivel de urgencia medica basado en sintomas y contexto.
    Retorna: leve | moderada | grave | emergencia
    """
    EMERGENCY_KW = ["infarto", "paro cardiaco", "convulsiones", "perdida de conciencia",
                    "anafilaxia", "shock", "sepsis", "hemorragia severa", "stroke",
                    "cardiac arrest", "unconscious", "not breathing"]
    GRAVE_KW = ["dolor pecho", "brazo izquierdo", "dificultad respiratoria",
                "meningitis", "apendicitis", "chest pain", "left arm pain",
                "difficulty breathing", "high fever", "fiebre muy alta"]

    combined = (symptoms + " " + context).lower()
    if any(kw in combined for kw in EMERGENCY_KW):
        return "emergencia — Llamar al 123 o ir a urgencias INMEDIATAMENTE."
    if any(kw in combined for kw in GRAVE_KW):
        return "grave — Buscar atencion medica pronto, no demorar mas de pocas horas."
    return "moderada — Consultar medico en las proximas 24-48 horas."


def get_drug_info(condition: str) -> str:
    """
    Busca informacion sobre medicamentos relacionados con una condicion medica
    en el libro Top 100 Drugs.
    """
    query = f"drugs treatment {condition} medication"
    candidates = retrieve(query, top_k=8)
    drug_chunks = [c for c in candidates if "Top 100 Drugs" in c.get("book", "")]

    if not drug_chunks:
        ranked = rerank(condition, candidates[:5], top_k=2)
        drug_chunks = ranked

    if not drug_chunks:
        return f"No se encontro informacion especifica de medicamentos para: {condition}."

    ranked = rerank(query, drug_chunks, top_k=2)
    parts = []
    for c in ranked:
        parts.append(f"[{c['book']} p.{c['page']}]\n{c['text'][:350]}")
    return "\n\n".join(parts)


def get_section(book_keyword: str, topic: str) -> str:
    """
    Recupera informacion de una seccion especifica de un libro.
    book_keyword: parte del nombre del libro (ej: 'Harrison', 'Oxford', 'Symptoms', 'Drugs')
    topic: tema a buscar dentro de ese libro
    """
    BOOK_MAP = {
        "harrison": "Harrison Principios De Medicina Interna 19 1",
        "oxford": "Oxford Handbook of Clinical Medicine 10th Edition",
        "symptoms": "Symptoms to diagnosis ",
        "drugs": "The Top 100 Drugs Clinical",
    }
    book_key = book_keyword.lower()
    matched_book = next((v for k, v in BOOK_MAP.items() if k in book_key), None)

    candidates = retrieve(topic, top_k=10)
    if matched_book:
        filtered = [c for c in candidates if matched_book in c.get("book", "")]
        if filtered:
            ranked = rerank(topic, filtered, top_k=3)
        else:
            ranked = rerank(topic, candidates, top_k=3)
    else:
        ranked = rerank(topic, candidates, top_k=3)

    enriched = enrich_chunks(ranked)
    if not enriched:
        return f"No se encontro informacion sobre '{topic}' en {book_keyword}."

    parts = []
    for c in enriched:
        parts.append(f"[{c['book']} | {c.get('seccion','?')} | p.{c['page']}]\n{c['text'][:400]}")
    return "\n\n".join(parts)


# Registro de herramientas disponibles para el agente
TOOLS: dict[str, dict] = {
    "search_symptoms": {
        "func": search_symptoms,
        "description": (
            "Busca en los libros medicos fragmentos relevantes para sintomas dados. "
            "Usar primero siempre que el usuario describa sintomas. "
            "Input: descripcion de sintomas en texto libre."
        ),
    },
    "assess_urgency": {
        "func": assess_urgency,
        "description": (
            "Evalua el nivel de urgencia medica. "
            "Usar despues de search_symptoms para determinar si es emergencia. "
            "Input: 'sintomas|||contexto_medico'"
        ),
    },
    "get_drug_info": {
        "func": get_drug_info,
        "description": (
            "Obtiene informacion de medicamentos para una condicion medica del libro Top 100 Drugs. "
            "Usar cuando el usuario pregunta por tratamientos o medicamentos. "
            "Input: nombre de la condicion medica."
        ),
    },
    "get_section": {
        "func": get_section,
        "description": (
            "Busca un tema especifico dentro de un libro concreto. "
            "Usar para profundizar en un libro especifico. "
            "Input: 'nombre_libro|||tema' (ej: 'Harrison|||infarto miocardio')"
        ),
    },
}


def execute_tool(name: str, input_text: str) -> str:
    """Ejecuta una tool por nombre y retorna el resultado como string."""
    if name not in TOOLS:
        return f"Herramienta '{name}' no existe. Disponibles: {list(TOOLS.keys())}"

    func = TOOLS[name]["func"]
    try:
        if name == "assess_urgency":
            parts = input_text.split("|||", 1)
            symptoms = parts[0].strip()
            context = parts[1].strip() if len(parts) > 1 else ""
            return func(symptoms, context)
        elif name == "get_section":
            parts = input_text.split("|||", 1)
            book = parts[0].strip()
            topic = parts[1].strip() if len(parts) > 1 else input_text
            return func(book, topic)
        else:
            return func(input_text)
    except Exception as e:
        return f"Error ejecutando {name}: {e}"


def tools_description() -> str:
    """Genera descripcion de todas las tools para el system prompt."""
    lines = []
    for name, meta in TOOLS.items():
        lines.append(f"- {name}: {meta['description']}")
    return "\n".join(lines)
