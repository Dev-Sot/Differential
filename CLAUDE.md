# MEDI-IA — Asistente Medico con RAG

Agente de diagnostico diferencial basado en libros medicos reales.
Usa FAISS + sentence-transformers + cross-encoder reranker + Claude API.

## Estructura del proyecto

```
MEDI-IA_Codigo_App/
├── src/
│   ├── rag/
│   │   ├── embeddings.py       Singleton modelo sentence-transformers
│   │   ├── retriever.py        Busqueda FAISS (top-10)
│   │   ├── reranker.py         Cross-encoder reranking (top-5)
│   │   ├── semantic_fallback.py Fallback cuando confianza baja
│   │   └── section_mapping.py  Mapeo pagina -> capitulo del libro
│   ├── prompts/
│   │   ├── diagnostico.txt     Prompt principal de diagnostico
│   │   ├── urgencia.txt        Clasificacion de urgencia
│   │   └── fallback.txt        Respuesta cuando no hay info suficiente
│   ├── agent.py                Orquestador: retrieve->rerank->generate
│   └── schemas.py              Modelos Pydantic (validacion E/S)
├── libros/                     PDFs de libros medicos
├── index/                      Indice FAISS + metadata.json
├── templates/index.html        UI del chat
├── tests/test_pipeline.py      Tests automatizados
├── app.py                      Flask API
├── ingest.py                   Script de ingesta de PDFs
├── .env                        API keys (NO subir a git)
├── .env.example                Template de variables
├── Makefile                    Comandos utiles
└── requirements.txt
```

## Comandos principales

```bash
make install    # Instalar dependencias
make ingest     # Procesar PDFs y construir indice FAISS
make run        # Iniciar servidor en localhost:5000
make test       # Ejecutar tests
make health     # Ver estado del sistema
```

## Agregar un libro nuevo

1. Copiar el PDF a `libros/`
2. Ejecutar `make ingest`
3. Si el servidor esta corriendo: `make reload`
4. Actualizar `src/rag/section_mapping.py` con los capitulos del nuevo libro

## Variables de entorno

Ver `.env.example`. La mas importante:
- `ANTHROPIC_API_KEY` — sin esto el sistema funciona con templates, con esto usa Claude

## Pipeline RAG

1. **Retrieve**: FAISS busca top-10 chunks por similitud coseno
2. **Rerank**: Cross-encoder (ms-marco-MiniLM-L-6-v2) reordena por relevancia real
3. **Enrich**: Section mapping agrega nombre del capitulo a cada chunk
4. **Fallback**: Si confianza < umbral, responde honestamente
5. **Generate**: Claude API (o template si no hay key) genera respuesta estructurada

## Libros indexados

- Harrison Principios De Medicina Interna 19 ed.
- Oxford Handbook of Clinical Medicine 10th ed.
- Symptom to Diagnosis
- The Top 100 Drugs Clinical

## Notas importantes

- El sistema NUNCA inventa informacion — solo usa los libros indexados
- Siempre incluye el disclaimer de consulta medica profesional
- Claude API es opcional — sin key funciona con template responses
- El reranker mejora significativamente la precision vs solo FAISS
