PYTHON = venv/Scripts/python.exe
PIP    = venv/Scripts/pip.exe

.PHONY: run ingest test install install-dev lint format typecheck reload health eval-full docker-build docker-run docker-stop docker-ingest sessions cleanup

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

## Instalar herramientas de desarrollo (ruff, black, mypy)
install-dev:
	$(PIP) install -r requirements-dev.txt

## Revisar estilo y errores estaticos (ruff)
lint:
	venv/Scripts/ruff.exe check .

## Formatear codigo (black)
format:
	venv/Scripts/black.exe .

## Chequeo de tipos (mypy)
typecheck:
	venv/Scripts/mypy.exe src app.py

## Evaluacion completa del pipeline RAG (40 queries, metricas Recall/MRR/Precision)
eval-full:
	$(PYTHON) -m src.evaluation_full

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

## Listar sesiones guardadas en SQLite
sessions:
	$(PYTHON) manage.py sessions

## Limpiar sesiones inactivas (default: 30 dias). Uso: make cleanup DAYS=7
cleanup:
	$(PYTHON) manage.py cleanup --days $(or $(DAYS),30)
