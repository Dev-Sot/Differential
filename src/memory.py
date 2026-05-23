"""
Memoria de conversacion para MEDI-IA.
Historial persistido en SQLite (memory.db) por sesion — sobrevive reinicios del servidor.
"""

import sqlite3
import os
from contextlib import contextmanager

MAX_TURNS = 10

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.db")


def _init_schema() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT NOT NULL,
            role    TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON turns(session)")
    conn.commit()
    conn.close()


_init_schema()


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_turn(session_id: str, role: str, content: str) -> None:
    """Agrega un turno al historial y recorta si supera MAX_TURNS."""
    with _db() as conn:
        conn.execute(
            "INSERT INTO turns (session, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        # Recortar: conservar solo los ultimos MAX_TURNS*2 turnos no-system
        rows = conn.execute(
            "SELECT id FROM turns WHERE session = ? AND role != 'system' ORDER BY id",
            (session_id,),
        ).fetchall()
        excess = len(rows) - MAX_TURNS * 2
        if excess > 0:
            ids_to_delete = [r["id"] for r in rows[:excess]]
            conn.execute(
                f"DELETE FROM turns WHERE id IN ({','.join('?'*len(ids_to_delete))})",
                ids_to_delete,
            )


def get_history(session_id: str) -> list[dict]:
    """Devuelve el historial completo de la sesion (system primero, luego por insercion)."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM turns WHERE session = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def set_system(session_id: str, system_prompt: str) -> None:
    """Establece el system prompt solo si la sesion no lo tiene aun."""
    with _db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM turns WHERE session = ? AND role = 'system'",
            (session_id,),
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO turns (session, role, content) VALUES (?, 'system', ?)",
                (session_id, system_prompt),
            )


def clear_session(session_id: str) -> None:
    """Elimina todo el historial de una sesion."""
    with _db() as conn:
        conn.execute("DELETE FROM turns WHERE session = ?", (session_id,))


def list_sessions() -> list[str]:
    """Lista todos los session_ids con historial guardado."""
    with _db() as conn:
        rows = conn.execute("SELECT DISTINCT session FROM turns").fetchall()
    return [r["session"] for r in rows]
