# Spec: Página de Evaluación Cuantitativa `/evaluate`

**Fecha:** 2026-05-24  
**Estado:** Aprobado

---

## Objetivo

Demostrar cuantitativamente que el cross-encoder reranker mejora el orden de los chunks recuperados por FAISS. La página debe ser visualmente impactante para una presentación académica.

---

## Arquitectura

### Archivos nuevos

| Archivo | Responsabilidad |
|---------|----------------|
| `src/evaluation.py` | Lógica del benchmark: corre queries, compara FAISS vs reranker, serializa resultados |
| `templates/evaluate.html` | Página visual con comparación lado a lado |
| `data/eval_snapshot.json` | Cache de resultados (generado en runtime, no commiteado) |

### Modificaciones a archivos existentes

| Archivo | Cambio |
|---------|--------|
| `app.py` | Agregar `GET /evaluate` y `POST /api/evaluate/run` |

---

## Benchmark

### Queries fijas (6 total)

Elegidas para maximizar el contraste FAISS cosine vs cross-encoder:

| # | Query | Contraste esperado |
|---|-------|-------------------|
| 1 | "dolor en el pecho que se irradia al brazo izquierdo" | FAISS trae cardiovascular genérico; reranker sube IAM |
| 2 | "fiebre alta con rigidez en el cuello" | Reranker discrimina meningitis de fiebre simple |
| 3 | "dificultad para respirar y tos con sangre" | Diferencia embolismo pulmonar vs neumonía |
| 4 | "dolor de cabeza severo de inicio súbito" | Reranker sube hemorragia subaracnoidea |
| 5 | "confusión mental en paciente diabético" | Reranker diferencia hipoglucemia vs CAD |
| 6 | "tratamiento primera línea hipertensión" | FAISS trae diagnóstico; reranker prioriza tratamiento |

### Función `run_benchmark()` en `src/evaluation.py`

```python
def run_benchmark() -> dict:
    # Para cada query:
    #   1. retrieve(query, top_k=10) → chunks con score FAISS
    #   2. rerank(query, chunks, top_k=5) → chunks reordenados con rerank_score
    #   3. Calcular delta de posición para cada chunk (posición FAISS vs posición reranker)
    #   4. Calcular si el top-1 cambió
    # Devuelve dict con: queries[], stats{}, timestamp, duration_s
```

### Estructura del snapshot JSON

```json
{
  "timestamp": "2026-05-24T10:32:00",
  "duration_s": 28.4,
  "stats": {
    "total_queries": 6,
    "top1_changed": 4,
    "avg_position_changes": 2.3
  },
  "queries": [
    {
      "query": "dolor en el pecho...",
      "faiss_results": [
        {"rank": 1, "score": 0.84, "book": "Harrison...", "page": 142, "text": "..."}
      ],
      "reranked_results": [
        {"rank": 1, "rerank_score": 7.2, "faiss_rank": 3, "delta": 2, "book": "...", "page": 201, "text": "..."}
      ]
    }
  ]
}
```

`delta` = posición FAISS original − posición reranker (positivo = subió, negativo = bajó, 0 = igual).

---

## UI: `templates/evaluate.html`

### Stat cards (fila superior, 4 cards)

- **Queries evaluadas:** 6
- **Top-1 mejorado:** N/6 (porcentaje)
- **Cambios de posición promedio:** X por query
- **Tiempo de benchmark:** Xs

### Por cada query — comparación lado a lado

```
Query: "dolor en el pecho que se irradia al brazo izquierdo"

FAISS top-5 (similitud coseno)     Reranker top-5 (cross-encoder)
──────────────────────────────     ──────────────────────────────
#1 │ Harrison p.142 │ 0.84 ████   #1 ↑+2 │ Harrison p.201 │ +7.2 █████
#2 │ Oxford p.89    │ 0.82 ████   #2  ─  │ Harrison p.142 │ +5.8 ████
#3 │ Harrison p.201 │ 0.80 ███    #3 ↓-1 │ Oxford p.89    │ +4.1 ███
#4 │ Harrison p.98  │ 0.78 ███    #4 ↑+1 │ Symptoms p.44  │ +2.3 ██
#5 │ Symptoms p.44  │ 0.77 ███    #5 NEW │ Harrison p.310 │ -1.2 █
                                  ✗ eliminado: Harrison p.98
```

Cada fila muestra: libro (abreviado), página, primeras 80 chars del texto (tooltip con completo), barra de progreso relativa.

### Indicadores visuales de cambio

- `↑+N` verde: el chunk subió N posiciones tras reranking
- `↓-N` rojo: bajó N posiciones
- `─` gris: sin cambio
- `NEW` azul: entró al top-5 desde posición > 5 en FAISS
- `✗ eliminado` rojo tenue: estaba en top-5 FAISS pero el reranker lo sacó

### Comportamiento de carga

1. `GET /evaluate` → render template con `has_snapshot` flag
2. Si `has_snapshot=True`: JS fetch `/api/evaluate/snapshot` → renderiza inmediatamente
3. Si `has_snapshot=False`: JS llama automáticamente `POST /api/evaluate/run` → muestra spinner con progreso SSE → renderiza al completar
4. Botón "Recalcular benchmark ↺": repite el paso 3 manualmente

### Sin índice FAISS

Muestra card de error: "Índice FAISS no encontrado. Ejecuta `make ingest` primero." — igual que el 503 del chat.

---

## Endpoints nuevos en `app.py`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/evaluate` | GET | Render `evaluate.html` |
| `/api/evaluate/snapshot` | GET | Lee y devuelve `data/eval_snapshot.json` (404 si no existe) |
| `/api/evaluate/run` | POST | Corre benchmark, guarda snapshot, devuelve resultado. Rate limit: 2/min |

`/api/evaluate/run` es síncrono (no SSE) — el frontend muestra un spinner mientras espera. El benchmark tarda ~20-40s dependiendo de si los modelos ya están cargados.

---

## Lo que NO incluye este spec

- Comparación con otros modelos de reranker (fuera de scope)
- Guardar histórico de benchmarks anteriores
- Permitir queries personalizadas (solo las 6 fijas)
- Autenticación separada para `/evaluate` (hereda `require_auth` si `AUTH_PASSWORD` está definido)

---

## Criterio de éxito

La página debe mostrar visualmente que en al menos 3/6 queries el top-1 chunk cambió después del reranking, con flechas y colores que lo hagan obvio a primera vista.
