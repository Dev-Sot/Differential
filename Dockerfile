FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero para aprovechar cache de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente
COPY . .

# Crear directorios necesarios y usuario no-root
RUN mkdir -p data index \
    && useradd -m -u 1000 medi \
    && chown -R medi:medi /app

USER medi

EXPOSE 5000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# El indice FAISS y la BD de sesiones deben montarse como volumenes:
#   -v ./index:/app/index     (indice FAISS pre-construido)
#   -v ./data:/app/data       (memory.db — sesiones SQLite)
# Para construir el indice desde cero:
#   docker exec <container> python ingest.py

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
