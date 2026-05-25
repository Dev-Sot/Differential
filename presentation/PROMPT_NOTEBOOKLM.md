# MEDI-IA Fase 2 — Fuente para NotebookLM / Gamma / Presentación

> Pega este documento completo en NotebookLM como fuente, o úsalo como prompt
> en Gamma.app ("Create presentation from text") para generar las diapositivas
> con la estética definida al final.

---

## ¿Qué es MEDI-IA?

MEDI-IA es un asistente médico de diagnóstico diferencial basado en inteligencia artificial generativa y Retrieval-Augmented Generation (RAG). El sistema combina 14 libros médicos reales indexados con un agente de razonamiento que utiliza el modelo Qwen2.5-7B de HuggingFace para producir diagnósticos fundamentados en literatura clínica reconocida internacionalmente.

El sistema opera en dos modos:
- **Modo ReAct** (con HF_TOKEN activo): Agente con razonamiento multi-paso Thought→Action→Observation, máximo 6 iteraciones, 4 herramientas especializadas, streaming en tiempo real.
- **Modo RAG Template** (sin token): Pipeline FAISS+BM25+Reranker sin LLM, respuestas basadas en chunks recuperados, funciona offline.

---

## Diapositiva 1 — Portada

**Título:** MEDI-IA — Asistente Médico con IA Generativa y RAG  
**Subtítulo:** Fase 2: Construcción, Mejoras y Resultados  

**Estadísticas clave a mostrar como badges:**
- 14 libros médicos indexados
- 136,228 chunks en el índice FAISS
- Modelo Qwen2.5-7B vía HuggingFace
- Recall@1: 97.1%
- 4 features innovadores de IA
- 100 tests automatizados

---

## Diapositiva 2 — ¿Qué construimos? Pipeline completo

**Pipeline de una consulta médica (izquierda a derecha):**

```
[Usuario] → [Guardrails] → [FAISS + BM25 + RRF] → [Cross-Encoder Reranker] → [Agente ReAct Qwen2.5-7B] → [Diagnóstico Diferencial]
```

**Dos columnas de detalle:**

Columna izquierda — Modo ReAct:
- Qwen2.5-7B vía HuggingFace Inference API (remoto, sin costo de GPU local)
- Bucle Thought → Action → Observation, máximo 6 iteraciones
- 4 herramientas: search_symptoms, assess_urgency, get_drug_info, get_section
- Memoria multi-turn persistida en SQLite por session_id
- Streaming Server-Sent Events (SSE): el usuario ve al agente "pensar" en tiempo real

Columna derecha — Modo RAG Template:
- FAISS IndexFlatIP (cosine similarity) + BM25 + Reciprocal Rank Fusion k=60
- Cross-Encoder reranker multilingüe (mMARCO, 26 idiomas)
- Threshold configurable RERANK_THRESHOLD=-3.0
- Fallback semántico cuando score del mejor chunk < umbral
- Funciona sin HF_TOKEN, ideal para demo sin costos de API

---

## Diapositiva 3 — Fase 1 vs Fase 2: El salto cualitativo

**Columna ANTES (Fase 1) — en rojo:**
- 4 libros médicos (Harrison, Oxford, Symptoms to Diagnosis, Top 100 Drugs)
- Modelo paraphrase-MiniLM-L12-v2 — 384 dimensiones, embeddings genéricos no optimizados para retrieval
- Búsqueda FAISS sola, sin BM25 ni fusión de rankings
- Chunks de 400 caracteres / overlap 80, sin filtro de basura
- Sin evaluación cuantitativa formal
- UI básica sin autenticación ni rate limiting
- Sin Docker, sin CI/CD, sin tests formales
- Recall@1 estimado: ~74%

**Columna DESPUÉS (Fase 2) — en verde/teal:**
- 14 libros médicos especializados — 136,228 chunks indexados
- intfloat/multilingual-e5-base — 768 dimensiones, optimizado específicamente para retrieval semántico
- Búsqueda híbrida FAISS + BM25 + Reciprocal Rank Fusion
- Chunks 600/120 caracteres, sentence-aware, con junk filter
- Dataset evaluación v1.3: 40 queries anotadas con métricas formales
- UI Dark Glassmorphism + autenticación + rate limiting + exportación PDF
- Docker + nginx + GitHub Actions CI + 100 tests automatizados
- Recall@1: 97.1% · MRR: 0.986

---

## Diapositiva 4 — La Base de Conocimiento: 14 Libros Médicos

**Estadísticas (mostrar como números grandes):**
- 14 libros indexados
- 136,228 chunks totales
- 768 dimensiones por vector (e5-base)
- 600 caracteres promedio por chunk

**Los 14 libros (tabla o lista):**
1. Harrison Principios de Medicina Interna 19ª Ed. — medicina general
2. Oxford Handbook of Clinical Medicine 10th Ed. — referencia clínica
3. Symptoms to Diagnosis — diagnóstico diferencial por síntoma
4. The Top 100 Drugs Clinical — farmacología práctica
5. Tintinalli Emergency Medicine Manual — urgencias y emergencias
6. Adams & Victor Principles of Neurology 8th Ed. — neurología
7. Harrison's Infectious Disease — infectología especializada
8. Infectious Diseases: A Clinical Short Course — infecciones clínicas
9. Compendio de Robbins y Cotran Patología — fisiopatología
10. Nelson Textbook of Pediatrics — pediatría
11. Kaplan-Sadock Pocket Handbook of Clinical Psychiatry — psiquiatría
12. Williams Obstetrics — obstetricia
13. Lange Clinical Cases 2017 — casos clínicos
14. ABC of Dermatology — dermatología

**Proceso de ingesta:**
- Chunking por oraciones (regex _SENT_RE), respeta contexto clínico
- Prefijos e5-base: "passage: {libro}: {texto}" en chunks, "query: " en búsquedas
- is_junk_chunk() elimina fragmentos con >50% dígitos (índices, referencias numéricas)
- Section mapping: mapeo estático página→capítulo por libro (section_mapping.py)
- Re-ingesta completa tarda ~45 minutos en CPU, resultado permanente en index/books.index

---

## Diapositiva 5 — Pipeline RAG Mejorado: e5-base + BM25 + RRF

**Seis mejoras técnicas clave:**

1. **intfloat/multilingual-e5-base** — Reemplazó paraphrase-MiniLM-L12-v2. Pasa de 384 a 768 dimensiones. Está específicamente pre-entrenado para tareas de recuperación semántica (no clasificación). Soporta 100+ idiomas. El prefijo "query: " en el momento de búsqueda activa el modo retrieval del modelo.

2. **BM25 + Reciprocal Rank Fusion** — rank-bm25 lazy-loaded desde metadata.json. RRF con k=60 fusiona los rankings de FAISS (semántico) y BM25 (léxico). Resuelve el problema crítico de términos médicos exactos que los embeddings difuminan: "metformina", "warfarina", "INR", códigos CIE-10.

3. **Cross-Encoder Reranker mMARCO** — mmarco-mMiniLMv2-L12-H384-v1, entrenado en MS MARCO multilingüe, 26 idiomas. Toma el Top-10 de FAISS+BM25 y genera un score de relevancia preciso. Score relevante > 0, irrelevante < -3.0 (configurable con RERANK_THRESHOLD).

4. **Chunk Size 400→600 / Overlap 80→120** — Chunks más grandes capturan más contexto clínico por fragmento. El overlap mayor evita cortes en medio de diagnósticos o descripciones de síntomas.

5. **Sentence-Aware Chunking** — El regex _SENT_RE respeta límites de oración (puntos, signos de interrogación, saltos de línea). No corta en medio de una oración clínica.

6. **Junk Filter** — is_junk_chunk() descarta fragmentos de texto con más del 50% de dígitos. Elimina páginas de referencias bibliográficas, índices numéricos, tablas de valores que contaminarían el índice.

---

## Diapositiva 6 — Resultados de Evaluación Cuantitativa

**Dataset v1.3: 40 queries anotadas manualmente**
- 35 queries médicas + 5 queries para validar guardrails
- Queries cubren 4 categorías: Síntomas→Diagnóstico, Urgencias y Triaje, Farmacología, Fisiopatología
- Cada query tiene libro(s) relevantes identificados manualmente
- Anotaciones validadas contra resultados reales del retriever

**Tabla comparativa (MOSTRAR COMO TABLA PRINCIPAL DE LA DIAPOSITIVA):**

| Métrica | MiniLM · 4 libros | e5-base · 4 libros | e5-base · 14 libros (ACTUAL) |
|---------|------------------|--------------------|------------------------------|
| Recall@1 | 74.3% | 91.4% | **97.1%** (+30.6%) |
| Recall@3 | 94.3% | 100% | **100%** |
| Recall@5 | 97.1% | 100% | **100%** |
| MRR | 0.8405 | 0.9571 | **0.9857** (+17.3%) |
| Precision@5 | 74.3% | 94.3% | **80.6%** |
| Guardrails | 100% | 100% | **100%** |

**Resultados por categoría (estado actual):**
- Síntomas → Diagnóstico: Recall@1=100%, MRR=1.000
- Urgencias y Triaje: Recall@1=100%, MRR=1.000
- Farmacología: Recall@1=90%, MRR=0.950 (1 edge case)
- Fisiopatología: Recall@1=100%, MRR=1.000

**El único fallo:** Q022 (metformina DM2) — Robbins aparece en #1 porque contiene patología de diabetes, no tratamiento con metformina. El libro correcto (Top 100 Drugs) aparece en Top-3. MRR=0.5 para esa query.

---

## Diapositiva 7 — Agente ReAct: Razonamiento Multi-Paso

**Ejemplo real de un ciclo ReAct (mostrar como trace visual):**

THOUGHT: "El paciente describe fiebre 39°C + tos productiva + dolor pleurítico. Necesito buscar en los libros los diagnósticos diferenciales de neumonía."

ACTION: search_symptoms("fiebre tos productiva dolor pleurítico adulto")

OBSERVATION: Harrison p.1023: "Neumonía bacteriana: fiebre >38.5°C, expectoración purulenta, consolidación lobar..." [score reranker: 0.87]

ACTION: assess_urgency("fiebre alta tos productiva|||neumonía probable")

OBSERVATION: URGENTE — signos de alarma: FR>30, SpO2<94%, confusión mental → considerar hospitalización

FINAL ANSWER: "Diagnóstico diferencial: 1) Neumonía adquirida en comunidad (alta probabilidad)..."

**Las 4 herramientas del agente:**

1. **search_symptoms** — Búsqueda RAG completa (FAISS+BM25+RRF+Reranker). Devuelve los 5 chunks más relevantes con libro, página y score. Es la herramienta principal.

2. **assess_urgency** — Clasifica síntomas en EMERGENCIA / URGENTE / CONSULTA / RUTINA. Incluye signos de alarma específicos y recomendación de nivel de atención. Usa separador "|||" para síntomas y contexto.

3. **get_drug_info** — Búsqueda específica en "The Top 100 Drugs Clinical". Devuelve mecanismo de acción, dosis, contraindicaciones, interacciones, efectos adversos.

4. **get_section** — Acceso directo a capítulo de libro por keyword. Formato: "harrison|||fiebre" → recupera el capítulo de Harrison sobre fiebre. Soporta todos los 14 libros.

**Parámetros del agente:**
- MAX_ITERATIONS = 6 ciclos
- Si no produce "Final Answer:" en 6 ciclos → último call forzado con todo el contexto acumulado
- Memoria: hasta 10 turnos por sesión, SQLite en data/memory.db
- Separador "|||" en tools de dos parámetros (manejo robusto si el LLM no lo usa)

---

## Diapositiva 8 — UI Redesign v2.0: Dark Glassmorphism

**Sistema de diseño implementado:**
- Fondo base: #090e1a · Surface: #0f1629 / #111d35
- Acento Emerald: #10b981 (hover states, elementos activos)
- Dark-first: :root define tokens oscuros, [data-theme="light"] como override
- Toggle luna/sol persistente en localStorage
- Font: Inter para UI, glassmorphism con backdrop-filter blur

**Componentes principales:**
- Topbar 52px con chip "RAG · 14 libros" con dot animado en verde (live)
- Sidebar 200px compacto con datos reales desde /api/health (chunks, modo, estado)
- Welcome screen: logo glass glow, tech badge dinámico, chips de symptom sugeridos
- Cards de respuesta: glass shadow, severity pills con íconos (check-circle, alert-triangle, alert-octagon, alert-circle)
- Historial de sesión con borrado individual (aparece en hover)

**Features de UX completados:**
- Copiar respuesta (Clipboard API)
- Input de voz Web Speech API (Chrome)
- Chips de seguimiento contextuales post-respuesta
- Sidebar móvil con backdrop y cierre touch
- Toasts de notificación con auto-dismiss
- Exportar sesión como PDF (/api/export/pdf con fpdf2)

**Seguridad y límites:**
- AUTH_PASSWORD en .env — protege toda la app con password
- Rate limiting: 10/min en query y stream, 5/min en PDF y login
- Session cookie con SECRET_KEY configurable
- Login con rate limit 5/min anti-brute force

---

## Diapositiva 9 — Los 4 Features Innovadores

**Feature 1: TTS Neural — Voz Médica Real**
edge-tts con voz es-ES-AlvaroNeural (voz humana sintética de alta calidad de Azure Cognitive Services).
- Backend: /api/tts en app.py — streaming audio via Thread + Queue + stream_with_context
- Frontend: MediaSource API para playback progresivo en Chrome/Edge + fallback blob URL
- _buildDoctorScript(data) genera un monólogo médico estructurado a partir de los campos de la respuesta (diagnóstico, párrafo explicativo, gravedad, recomendación)
- El fetch de TTS inicia ANTES de renderizar la tarjeta de respuesta para reducir latencia percibida
- Toggle global "manos libres" en topbar + botón de reproducción por tarjeta individual

**Feature 2: Perfil Clínico del Paciente**
Contexto persistente de sesión con información clínica del usuario.
- sessionStorage (persiste mientras la pestaña esté abierta, no entre sesiones)
- Campos: alergias, medicamentos actuales, condiciones crónicas
- Chips horizontales para agregar/quitar items de cada campo
- Inyección silenciosa en cada query: "[Paciente: alergias=penicilina, medicamentos=metformina 850mg, condiciones=DM tipo 2]"
- Modal con botón X para cerrar + "Saltar por ahora" + "Guardar perfil"
- checkProfileOnLoad() propone configurar el perfil si no hay uno guardado

**Feature 3: Mapa Corporal SVG Interactivo**
Drawer lateral derecho 320px con figura anatómica clicable.
- 15 zonas frontales + 9 zonas dorsales (toggle Frontal/Dorsal)
- SVG inline con data-zone y data-label en cada región (ellipse/rect)
- Al seleccionar zonas aparece una tarjeta de contexto en el chat con las zonas marcadas
- Inyección en la siguiente query: "[Zonas afectadas: pecho, abdomen, hombro derecho]"
- Chips con botón × individual por zona + "Limpiar todo"
- Las zonas se limpian automáticamente después de enviar la consulta

**Feature 4: Visualización del Pipeline RAG**
Panel colapsable que aparece debajo de cada respuesta del agente.
- Animación CSS con max-height: 0 → 1200px
- 3 pasos visuales: FAISS retrieval → Reranker → Síntesis LLM
- Para cada chunk recuperado: libro, número de página, score FAISS, score reranker, preview del texto
- Barras de progreso que muestran el delta entre score FAISS y score reranker
- Datos reales de data.rag_chunks que viene en la respuesta del servidor
- Permite al usuario entender exactamente qué libros y páginas fundamentaron el diagnóstico

---

## Diapositiva 10 — Stack Técnico y Deploy de Producción

**Backend Python:**
- Flask 3.x + Gunicorn (WSGI para producción)
- flask-limiter: 10/min en /api/query y /api/stream, 5/min en /api/export/pdf y /auth/login
- Pydantic: ConsultaRequest, DiagnosticoResponse, ErrorResponse — validación de entrada/salida
- SQLite para memoria multi-turn (max 10 turnos/sesión, preserva system prompt siempre)
- HuggingFace InferenceClient para Qwen2.5-7B (llamada remota, sin GPU local)
- edge-tts para síntesis de voz neural

**Stack ML / Retrieval:**
- FAISS IndexFlatIP — cosine similarity con vectores normalizados L2, 768 dimensiones
- sentence-transformers: intfloat/multilingual-e5-base (singletons lazy, se cargan en primer request)
- rank-bm25: BM25Okapi lazy-loaded desde metadata.json (136,228 documentos)
- CrossEncoder: mmarco-mMiniLMv2-L12-H384-v1 multilingüe (26 idiomas, ~120MB)

**Deploy:**
- Docker con imagen Python 3.11 slim
- docker-compose con volúmenes para index/ y data/
- nginx como reverse proxy con proxy_buffering off para el endpoint SSE /api/stream
- GitHub Actions CI: lint con flake8 + tests pytest en cada push a main
- Makefile con targets: install, ingest, run, test, health, reload, sessions, cleanup, docker-build, docker-run

**Estructura de código:**
```
app.py                    Flask app, endpoints, logging con request ID
src/agent.py              Orquestador: decide ReAct vs RAG
src/agent_loop.py         Bucle ReAct + generador SSE
src/guardrails.py         Filtro regex pre-LLM
src/llm.py                HuggingFace InferenceClient
src/memory.py             Historial SQLite multi-turn
src/rag/embeddings.py     Singleton e5-base
src/rag/retriever.py      FAISS + BM25 + RRF
src/rag/reranker.py       CrossEncoder singleton
src/rag/bm25_retriever.py BM25 lazy-loaded
tests/                    100 tests, 8 archivos pytest
```

---

## Diapositiva 11 — Métricas, Observabilidad y Calidad

**Números del sistema (mostrar como stats grandes):**
- 100 tests automatizados
- 40 queries en dataset de evaluación
- 8 endpoints API
- 6 iteraciones máximas del agente ReAct

**Dashboard /metrics:**
- Queries por hora (últimas 24 horas, gráfico de barras)
- Latencia promedio por endpoint en milisegundos
- Uptime del servidor desde último restart
- Feedback 👍/👎 guardado en SQLite con session_id y timestamp

**Dashboard /evaluate:**
- Benchmark con 6 queries representativas
- Comparación visual FAISS vs Reranker (barras min-max normalizadas)
- Recall@1, Recall@3, Recall@5, MRR, Precision@5 por categoría
- Endpoint /api/evaluate/full sirve data/eval_full_results.json

**Logging estructurado (formato Docker-friendly):**
```
2026-05-25T14:32:01 INFO  rid=a3f7b2c1 POST /api/stream 200 12ms
2026-05-25T14:32:04 INFO  rid=a3f7b2c1 stream_ms=3241 session=4e8d21a0 iters=4
2026-05-25T14:33:05 WARN  rid=c1a2b3d4 auth_fail ip=192.168.1.10
```
Cada request tiene un ID de 8 chars (rid) para correlacionar logs.

**Tests por archivo:**
- test_guardrails.py: 26 tests — lógica pura, sin mocks, rápido
- test_tools.py: 31 tests — mocks FAISS, prueba las 4 herramientas del agente
- test_memory.py: 26 tests — SQLite con tmp_path, prueba multi-turn y cleanup
- test_api.py: 19 tests — endpoints Flask completos

---

## Diapositiva 12 — Conclusiones y Próximos Pasos

**Resumen de lo construido en Fase 2:**

MEDI-IA Fase 2 pasó de un prototipo básico a un sistema médico de asistencia diagnóstica completo con:
- Pipeline RAG híbrido de nivel académico (FAISS+BM25+RRF+CrossEncoder)
- Agente de razonamiento multi-paso con herramientas especializadas
- Base de conocimiento de 14 libros médicos y 136,228 fragmentos indexados
- Evaluación cuantitativa formal: Recall@1=97.1%, MRR=0.986
- Interfaz de producción con 4 features innovadores de IA
- Stack completo de producción: Docker, nginx, CI/CD, 100 tests

**El único fallo conocido:** Q022 metformina — Robbins aparece en #1 por patología de diabetes. Está en Top-3, MRR=0.5 para esa query.

**Próximas mejoras planeadas:**
1. HyDE (Hypothetical Document Embeddings) — requiere HF_TOKEN activo para generar respuesta hipotética antes de buscar
2. Multi-query retrieval — 3 variantes de la query, merge con RRF
3. Estos dos cambios requieren re-ingesta parcial o ajuste del pipeline de búsqueda

---

## Guía de estética para generar la presentación

Si usas este documento en Gamma.app, Beautiful.ai, o le pides a una IA que genere las diapositivas, incluye estas instrucciones de estilo:

**Paleta de colores:**
- Fondo: #060b14 (casi negro azulado)
- Superficies/cards: #0e1e33
- Color principal/acento: #00d4b8 (teal/cyan)
- Secundario: #3b82f6 (azul)
- Éxito/positivo: #22c55e (verde)
- Advertencia: #f59e0b (amarillo)
- Error/negativo: #ef4444 (rojo)
- Texto principal: #e8f4f8
- Texto secundario/muted: #7ca6c0
- Bordes: #1a3550

**Tipografía:** Sora (títulos, cuerpo) + DM Mono (código, datos, badges)

**Estilo general:**
- Dark glassmorphism — fondos oscuros con cards translúcidas
- Grid de cuadrícula sutil en el fondo (líneas #1a3550 cada 60px)
- Barra de progreso teal→azul en la parte superior
- Badges/chips con borde de color suave y fondo semi-transparente del mismo color
- Tablas con borde inferior sutil, header en teal uppercase monospace
- Comparaciones Fase1/Fase2: columna roja vs columna teal
- Stats grandes: número en gradiente teal→azul, label en muted
- Pipeline: pasos conectados con flechas → en teal
- Código inline: fondo cyan semi-transparente, texto cyan

**Tono de la presentación:**
Técnico-académico pero visualmente impactante. Los datos cuantitativos (97.1%, 136,228 chunks, MRR 0.986) deben ser protagonistas. La comparación Fase 1 → Fase 2 es el argumento central: mostramos mejora medible y sistemática.

---

*Documento generado para MEDI-IA Fase 2 — Mayo 2026*
