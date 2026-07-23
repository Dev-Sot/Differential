"""
Modo de practica de casos clinicos — el giro de interaccion de Differential.

En vez de "usuario describe sintomas -> IA da un diagnostico", el sistema
presenta un caso y es el USUARIO quien propone su diferencial. El sistema
evalua/coach ea:

  - Con HF_TOKEN (modo LLM): el agente compara la respuesta del usuario
    contra el diferencial de referencia y da feedback especifico.
  - Sin HF_TOKEN (modo autoevaluacion): se revela el diferencial de
    referencia + el punto de ensenanza y el propio usuario se autocalifica
    (mismo patron que apps de repeticion espaciada tipo Anki — no requiere
    IA para ser pedagogicamente valido).

El banco de casos (data/case_bank.json) es contenido original escrito para
este proyecto, no extraido de los libros indexados — evita el problema de
copyright que tendria generar "casos" a partir del texto de los PDFs.
"""

import json
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime

from src import memory as memory_mod

_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CASE_BANK_PATH = os.path.join(_BASE_DIR, "data", "case_bank.json")

_cases: list[dict] | None = None


def _load_cases() -> list[dict]:
    global _cases
    if _cases is None:
        with open(CASE_BANK_PATH, encoding="utf-8") as f:
            _cases = json.load(f)
    return _cases


def get_case(case_id: str) -> dict | None:
    return next((c for c in _load_cases() if c["id"] == case_id), None)


def get_random_case(exclude_ids: list[str] | None = None) -> dict:
    cases = _load_cases()
    pool = [c for c in cases if c["id"] not in (exclude_ids or [])] or cases
    return random.choice(pool)


def list_specialties() -> list[str]:
    return sorted({c["specialty"] for c in _load_cases()})


def public_case(case: dict) -> dict:
    """Version del caso segura para enviar al cliente ANTES de que responda
    (sin el diferencial de referencia ni el punto de ensenanza)."""
    return {"id": case["id"], "specialty": case["specialty"], "vignette": case["vignette"]}


def evaluate_answer(case: dict, user_answer: str) -> dict:
    """Evalua la respuesta del usuario. Usa el agente LLM si HF_TOKEN esta
    definido; si no, devuelve el material para autoevaluacion."""
    reference = {
        "correct_dx": case["correct_dx"],
        "reference_differential": case["reference_differential"],
        "teaching_point": case["teaching_point"],
    }

    if os.getenv("HF_TOKEN"):
        try:
            return _evaluate_with_llm(case, user_answer, reference)
        except Exception:
            pass  # si el LLM falla, no rompemos la practica — cae a autoevaluacion

    return {
        "mode": "self_assessment",
        **reference,
    }


def _evaluate_with_llm(case: dict, user_answer: str, reference: dict) -> dict:
    from src.llm import chat

    prompt = (
        f"Caso clinico: {case['vignette']}\n\n"
        f"El estudiante propuso este diferencial: \"{user_answer}\"\n\n"
        f"Diferencial de referencia: {', '.join(d['dx'] for d in case['reference_differential'])}\n"
        f"Diagnostico correcto: {case['correct_dx']}\n\n"
        "Evalua la respuesta del estudiante en espanol: que tan cerca estuvo del "
        "diferencial correcto, que le falto o sobro, y da feedback breve tipo tutor "
        "socratico (no le repitas la respuesta completa, guialo). Maximo 120 palabras."
    )
    feedback = chat([{"role": "user", "content": prompt}], max_tokens=300)
    return {"mode": "llm_coach", "feedback": feedback, **reference}


# ── Persistencia de intentos (case_attempts) ────────────────────────────────

@contextmanager
def _db():
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
            CREATE TABLE IF NOT EXISTS case_attempts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                case_id       TEXT NOT NULL,
                specialty     TEXT NOT NULL,
                user_answer   TEXT NOT NULL,
                self_rating   TEXT,
                mode          TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user ON case_attempts(user_id)")


_init_schema()


def record_attempt(
    user_id: int, case_id: str, specialty: str, user_answer: str, mode: str, self_rating: str | None = None
) -> int:
    """Guarda el intento y devuelve su id (para poder autocalificarlo despues)."""
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO case_attempts (user_id, case_id, specialty, user_answer, self_rating, mode, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, case_id, specialty, user_answer, self_rating, mode, datetime.now(UTC).isoformat()),
        )
        return cur.lastrowid


def rate_attempt(attempt_id: int, user_id: int, self_rating: str) -> bool:
    """Guarda la autocalificacion de un intento existente. Devuelve False si no existe/no es del usuario."""
    with _db() as conn:
        cur = conn.execute(
            "UPDATE case_attempts SET self_rating = ? WHERE id = ? AND user_id = ?",
            (self_rating, attempt_id, user_id),
        )
        return cur.rowcount > 0


def get_progress(user_id: int) -> dict:
    """Resumen de progreso: intentos totales, por especialidad, y tasa de aciertos autocalificados."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT specialty, self_rating FROM case_attempts WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    total = len(rows)
    rated = [r for r in rows if r["self_rating"]]
    correct = sum(1 for r in rated if r["self_rating"] == "correct")

    by_specialty: dict[str, dict] = {}
    for r in rows:
        s = by_specialty.setdefault(r["specialty"], {"total": 0, "correct": 0, "rated": 0})
        s["total"] += 1
        if r["self_rating"]:
            s["rated"] += 1
            if r["self_rating"] == "correct":
                s["correct"] += 1

    weak_areas = sorted(
        (s for s in by_specialty.items() if s[1]["rated"] >= 2),
        key=lambda kv: kv[1]["correct"] / kv[1]["rated"],
    )

    return {
        "total_attempts": total,
        "rated_attempts": len(rated),
        "correct_attempts": correct,
        "accuracy": round(correct / len(rated), 2) if rated else None,
        "by_specialty": by_specialty,
        "weakest_specialty": weak_areas[0][0] if weak_areas else None,
    }
