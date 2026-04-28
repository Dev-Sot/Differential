"""
Memoria de conversacion para MEDI-IA.
Mantiene el historial por sesion para contexto multi-turn.
"""

from collections import defaultdict

MAX_TURNS = 10  # maximo de intercambios a recordar por sesion

_sessions: dict[str, list[dict]] = defaultdict(list)


def add_turn(session_id: str, role: str, content: str) -> None:
    """Agrega un turno al historial de la sesion."""
    _sessions[session_id].append({"role": role, "content": content})
    # Mantener solo los ultimos MAX_TURNS turnos (preservar system)
    history = _sessions[session_id]
    system = [m for m in history if m["role"] == "system"]
    rest = [m for m in history if m["role"] != "system"]
    if len(rest) > MAX_TURNS * 2:
        rest = rest[-(MAX_TURNS * 2):]
    _sessions[session_id] = system + rest


def get_history(session_id: str) -> list[dict]:
    """Devuelve el historial completo de la sesion."""
    return list(_sessions[session_id])


def set_system(session_id: str, system_prompt: str) -> None:
    """Establece el system prompt de la sesion (solo una vez)."""
    history = _sessions[session_id]
    if not any(m["role"] == "system" for m in history):
        _sessions[session_id] = [{"role": "system", "content": system_prompt}] + history


def clear_session(session_id: str) -> None:
    """Limpia el historial de una sesion."""
    _sessions.pop(session_id, None)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
