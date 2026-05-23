PYTHON = venv/Scripts/python.exe
PIP    = venv/Scripts/pip.exe

.PHONY: run ingest test install reload health docker-build docker-run docker-stop docker-ingest

## Iniciar servidor Flask
run:
	$(PYTHON) app.py

## Procesar PDFs y construir indice FAISS
ingest:
	$(PYTHON) ingest.py

## Ejecutar tests
test:
	venv/Scripts/pytest.exe tests/ -v

## Instalar dependencias
install:
	$(PIP) install -r requirements.txt

## Recargar indice sin reiniciar servidor (requiere servidor activo)
reload:
	curl -X POST http://localhost:5000/api/reload

## Ver estado del sistema
health:
	curl http://localhost:5000/api/health

## Docker: construir imagen
docker-build:
	docker build -t medi-ia .

## Docker: levantar con docker compose (detached)
docker-run:
	docker compose up -d

## Docker: bajar contenedores
docker-stop:
	docker compose down

## Docker: construir indice FAISS dentro del contenedor
docker-ingest:
	docker compose exec medi-ia python ingest.py
