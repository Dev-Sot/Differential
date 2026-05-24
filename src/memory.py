"""
Memoria de conversacion para MEDI-IA.
Historial persistido en SQLite (memory.db) por sesion — sobrevive reinicios del servidor.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone

MAX_TURNS = 10

_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)

# Configurable via MEMORY_DB_PATH para deploy personalizado
DB_PATH = os.getenv("MEMORY_DB_PATH", os.path.join(_DATA_DIR, "memory.db"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session   TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT NOT NULL,
            condicion TEXT,
            rating    INTEGER NOT NULL,
            ts        TEXT NOT NULL
        )
    """)
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


def _touch_session(conn: sqlite3.Connection, session_id: str) -> None:
    """Actualiza last_seen de la sesion (upsert)."""
    conn.execute(
        "INSERT INTO sessions (session, last_seen) VALUES (?, ?)"
        " ON CONFLICT(session) DO UPDATE SET last_seen = excluded.last_seen",
        (session_id, _now_iso()),
    )


def add_turn(session_id: str, role: str, content: str) -> None:
    """Agrega un turno al historial y recorta si supera MAX_TURNS."""
    with _db() as conn:
        conn.execute(
            "INSERT INTO turns (session, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        _touch_session(conn, session_id)
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
            _touch_session(conn, session_id)


def clear_session(session_id: str) -> None:
    """Elimina todo el historial de una sesion."""
    with _db() as conn:
        conn.execute("DELETE FROM turns WHERE session = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session = ?", (session_id,))


def list_sessions() -> list[str]:
    """Lista todos los session_ids con historial guardado."""
    with _db() as conn:
        rows = conn.execute("SELECT DISTINCT session FROM turns").fetchall()
    return [r["session"] for r in rows]


def cleanup_old_sessions(days: int = 30) -> int:
    """
    Elimina sesiones sin actividad en los ultimos `days` dias.
    Retorna el numero de sesiones eliminadas.
    """
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    with _db() as conn:
        old = conn.execute(
            "SELECT session FROM sessions WHERE last_seen < ?",
            (cutoff_iso,),
        ).fetchall()
        stale_ids = [r["session"] for r in old]
        if stale_ids:
            placeholders = ",".join("?" * len(stale_ids))
            conn.execute(f"DELETE FROM turns WHERE session IN ({placeholders})", stale_ids)
            conn.execute(f"DELETE FROM sessions WHERE session IN ({placeholders})", stale_ids)
    return len(stale_ids)


def save_feedback(session_id: str, condicion: str, rating: int) -> None:
    """Guarda una valoracion (1=positivo, -1=negativo) para una condicion diagnosticada."""
    with _db() as conn:
        conn.execute(
            "INSERT INTO feedback (session, condicion, rating, ts) VALUES (?, ?, ?, ?)",
            (session_id, condicion or "", rating, _now_iso()),
        )


def get_feedback_stats() -> dict:
    """Resumen global de valoraciones: total, positivos, negativos."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT rating, COUNT(*) AS cnt FROM feedback GROUP BY rating"
        ).fetchall()
    total    = sum(r["cnt"] for r in rows)
    positive = next((r["cnt"] for r in rows if r["rating"] == 1),  0)
    negative = next((r["cnt"] for r in rows if r["rating"] == -1), 0)
    return {"total": total, "positive": positive, "negative": negative}


def session_stats() -> list[dict]:
    """Devuelve estadisticas de todas las sesiones: id, turns y last_seen."""
    with _db() as conn:
        rows = conn.execute("""
            SELECT t.session,
                   COUNT(t.id)  AS turns,
                   s.last_seen
            FROM turns t
            LEFT JOIN sessions s ON s.session = t.session
            GROUP BY t.session
            ORDER BY s.last_seen DESC
        """).fetchall()
    return [{"session": r["session"], "turns": r["turns"], "last_seen": r["last_seen"]} for r in rows]
