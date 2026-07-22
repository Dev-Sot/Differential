"""Metricas en memoria del proceso (queries/hora, latencia, errores, uptime).

Nota: al vivir en memoria de un solo proceso, estos contadores no se comparten
entre workers de gunicorn ni sobreviven un reinicio. Ver hallazgo de la
auditoria (rate limiting / metricas no compartidas entre workers) — mover a
un store compartido (Redis) es el siguiente paso si se despliega con >1 worker.
"""

import threading
import time
from collections import deque
from datetime import datetime, timedelta

_mtx = threading.Lock()
_query_ts = deque(maxlen=10_000)   # timestamps (float) de queries completadas
_lat_log = deque(maxlen=2_000)     # (ts: float, ms: int) por query
_err_count = [0]
_start_mono = time.monotonic()


def record_query(latency_ms: int) -> None:
    now = time.time()
    with _mtx:
        _query_ts.append(now)
        _lat_log.append((now, latency_ms))


def record_error() -> None:
    with _mtx:
        _err_count[0] += 1


def snapshot(feedback_stats: dict) -> dict:
    """Arma el payload de /api/metrics a partir de los contadores actuales."""
    now = time.time()
    cutoff_1h = now - 3_600
    cutoff_24h = now - 86_400

    with _mtx:
        q_1h = sum(1 for ts in _query_ts if ts > cutoff_1h)
        q_24h = sum(1 for ts in _query_ts if ts > cutoff_24h)
        q_total = len(_query_ts)
        lats_1h = [ms for ts, ms in _lat_log if ts > cutoff_1h]
        errors = _err_count[0]
        hourly = [0] * 24
        for ts in _query_ts:
            age_h = (now - ts) / 3600
            if 0 <= age_h < 24:
                hourly[23 - int(age_h)] += 1

    avg_ms = round(sum(lats_1h) / len(lats_1h)) if lats_1h else 0
    p95_ms = 0
    if lats_1h:
        sorted_lats = sorted(lats_1h)
        p95_ms = sorted_lats[max(0, int(len(sorted_lats) * 0.95) - 1)]

    now_dt = datetime.now()
    labels = [(now_dt - timedelta(hours=23 - i)).strftime("%H:00") for i in range(24)]

    return {
        "queries_last_1h": q_1h,
        "queries_last_24h": q_24h,
        "queries_session_total": q_total,
        "avg_latency_ms": avg_ms,
        "p95_latency_ms": p95_ms,
        "error_count": errors,
        "uptime_s": int(time.monotonic() - _start_mono),
        "hourly_last_24h": hourly,
        "hourly_labels": labels,
        "feedback_total": feedback_stats["total"],
        "feedback_positive": feedback_stats["positive"],
        "feedback_negative": feedback_stats["negative"],
    }
