"""
Configuracion de Gunicorn para MEDI-IA en produccion.

Workers: 2 con preload_app=True — los modelos ML (FAISS + cross-encoder)
se cargan una vez y se comparten entre workers via fork (copy-on-write).
Aumentar workers solo si tienes RAM suficiente (~1.5 GB por worker).

SSE (/api/stream): los workers sync manejan streaming correctamente.
Si usas un proxy nginx en frente, agrega:
    proxy_buffering off;
    proxy_cache off;
en el location de /api/stream.
"""

import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

workers = 2
worker_class = "sync"
threads = 2          # hilos por worker para requests concurrentes cortos
timeout = 120        # permite inferencia lenta del cross-encoder y LLM
keepalive = 5

preload_app = True   # carga modelos ML una vez antes de forkear workers

# Logs a stdout/stderr (Docker-friendly)
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sus'


def post_worker_init(worker):
    """Arranca el cron de limpieza solo en el primer worker (age==1) para no duplicarlo."""
    if getattr(worker, "age", 1) == 1:
        from app import _start_cleanup_cron
        _start_cleanup_cron()
