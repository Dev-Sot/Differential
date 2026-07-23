"""
Autenticacion de usuarios reales para Differential.

Reemplaza el AUTH_PASSWORD unico compartido por cuentas individuales
(email + password) — necesario para poder asociar progreso y casos
practicados a una persona en vez de a una sesion anonima.
"""

import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from src import memory as memory_mod

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


class AuthError(ValueError):
    """Error de validacion visible al usuario (email invalido, password corta, etc)."""


@contextmanager
def _db():
    # Referencia memory_mod.DB_PATH en el momento de la llamada (no al importar)
    # para que los tests puedan redirigir la DB via monkeypatch.setattr.
    conn = sqlite3.connect(memory_mod.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_schema() -> None:
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
        """)


_init_schema()


def create_user(email: str, password: str) -> int:
    """Crea una cuenta nueva. Devuelve el id del usuario. Lanza AuthError si algo es invalido."""
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise AuthError("Correo invalido.")
    if len(password or "") < MIN_PASSWORD_LEN:
        raise AuthError(f"La contrasena debe tener al menos {MIN_PASSWORD_LEN} caracteres.")

    with _db() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise AuthError("Ya existe una cuenta con ese correo.")
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, generate_password_hash(password), datetime.now(UTC).isoformat()),
        )
        return cur.lastrowid


def verify_user(email: str, password: str) -> int | None:
    """Devuelve el user_id si el email/password son correctos, None si no."""
    email = (email or "").strip().lower()
    with _db() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    if row and check_password_hash(row["password_hash"], password or ""):
        return row["id"]
    return None


def get_user(user_id: int) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None
