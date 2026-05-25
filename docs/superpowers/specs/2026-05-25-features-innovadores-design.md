# MEDI-IA — Features Innovadores v1.0

**Fecha:** 2026-05-25
**Alcance:** 4 features nuevos — perfil clínico, TTS, cuerpo humano interactivo, visualización pipeline RAG
**Archivos modificados:** Solo `templates/index.html` (HTML + CSS + JS). Sin cambios en Python.
**Storage:** `sessionStorage` para perfil, `localStorage` para estado TTS.

---

## Feature 1 — Perfil Clínico Modal

### Comportamiento
- Aparece automáticamente en el primer load si `sessionStorage.getItem('medi-ia-profile')` es null.
- Un botón "Mi perfil" en el sidebar lo reabre en cualquier momento.
- Botón "Guardar perfil" persiste en sessionStorage. Botón "Saltar por ahora" cierra sin guardar.

### Campos
| Campo | Tipo | Storage key |
|-------|------|-------------|
| Nombre | texto libre | `nombre` |
| Edad | número | `edad` |
| Alergias | chips (Enter para agregar, × para quitar) | `alergias: string[]` |
| Medicamentos actuales | chips | `medicamentos: string[]` |
| Condiciones previas | chips | `condiciones: string[]` |
| Embarazada | toggle boolean | `embarazada` |

### Schema sessionStorage
```json
{
  "nombre": "Ana",
  "edad": 32,
  "alergias": ["penicilina", "ibuprofeno"],
  "medicamentos": ["atenolol 50mg"],
  "condiciones": ["hipertensión"],
  "embarazada": false
}
```

### Inyección en query
Antes de enviar a `/api/query` o `/api/stream`, se construye un prefijo invisible al usuario:

```
[Paciente: Ana, 32 años. Alergias: penicilina, ibuprofeno. Medicamentos: atenolol 50mg. Condiciones: hipertensión.]
```

Si el perfil está vacío o fue saltado, no se agrega prefijo. La inyección se hace en la función JS que construye el body del fetch, no en el `<textarea>` visible.

### UI
- Modal centrado, fondo `backdrop-filter: blur(8px)` sobre `rgba(0,0,0,0.6)`
- Superficie `var(--surface)`, borde `var(--border-em)`, `border-radius: 16px`
- Chips con botón × para eliminar, acento emerald
- Consistente con dark glassmorphism del resto de la app

---

## Feature 2 — Respuesta por Voz (TTS)

### API
Web Speech API (`window.speechSynthesis`) — puro browser, sin dependencias externas.
Voz seleccionada: primera voz disponible con `lang` que empiece por `es` (es-ES, es-MX, etc.).

### Toggle global (hands-free)
- Ícono Lucide `volume-2` en el topbar, junto al toggle de tema.
- Estado activo: ícono pulsa con color `var(--em)`.
- Cuando está activo: cada respuesta se lee automáticamente al completarse el streaming.
- Se detiene si el usuario envía una nueva consulta.
- Estado persistido en `localStorage` key `medi-tts-enabled`.

### Botón por respuesta
- Ícono Lucide `volume-2` pequeño en el footer de cada card (junto al botón copiar).
- Click → lee esa respuesta. Click de nuevo → detiene.
- Ícono cambia a `volume-x` mientras está leyendo.

### Texto a leer
Solo el texto limpio de la respuesta: sin fragmentos RAG, sin scores, sin metadatos.
Si el texto supera 500 palabras, se lee solo el primer párrafo + sección de recomendación (texto tras "**Recomendación**" o "**Conclusión**" si existe).

### Compatibilidad
Solo Chrome/Edge tienen implementación completa de SpeechSynthesis con voces en español. Si la API no está disponible o no hay voz en español, los botones TTS se ocultan silenciosamente.

---

## Feature 3 — Cuerpo Humano Interactivo

### Trigger
Botón con ícono Lucide `map-pin` en la barra de input (junto al micrófono). Abre un drawer desde la derecha.

### Drawer
- Ancho: `320px` en desktop, `100%` en móvil
- Desliza desde la derecha con `transform: translateX` + `transition`
- Cierre: click en overlay oscuro o botón × en header del drawer

### SVG del cuerpo humano
- Dos vistas: **Frontal** y **Dorsal** — toggle en la parte superior
- SVG inline en el HTML, con `<path>` o `<ellipse>` por zona
- Cambio de vista con transición de opacidad

**Zonas frontal (15):**
cabeza, cuello, pecho, abdomen, pelvis, hombro-izq, hombro-der, brazo-izq, brazo-der, antebrazo-izq, antebrazo-der, muslo-izq, muslo-der, pierna-izq, pierna-der

**Zonas dorsal (10):**
cabeza-post, cuello-post, espalda-alta, espalda-baja, gluteos, muslo-post-izq, muslo-post-der, pierna-post-izq, pierna-post-der

### Interacción
- Click en zona → zona se ilumina (`fill: rgba(16,185,129,0.35)`, glow con `filter: drop-shadow`)
- El nombre de la zona aparece como chip en sección "Zonas marcadas" dentro del drawer
- Click de nuevo en zona marcada → la desmarca y quita el chip
- Las zonas marcadas persisten mientras dure la sesión del browser

### Integración con chat
- Las zonas marcadas se muestran como chips cyan debajo del textarea
- Al enviar la consulta, se construye el prefijo: `[Zonas afectadas: pecho, brazo izquierdo.]`
- Se combina con el perfijo del perfil clínico si existe:
  ```
  [Paciente: Ana, 32 años. Alergias: penicilina.] [Zonas afectadas: pecho, brazo izquierdo.]
  ```

---

## Feature 4 — Visualización del Pipeline RAG

### Trigger
Botón "Ver cómo lo procesé" en el footer de cada card de respuesta AI.
Al hacer click, un panel se expande debajo de la card con animación `max-height`.

### Datos
Los datos ya vienen en el campo `trazabilidad` de la respuesta API — no se requieren cambios en backend.

### Contenido del panel (3 pasos animados en secuencia)
Los pasos aparecen con un delay de `200ms` entre ellos para dar sensación de proceso.

**Paso 1 — Recuperación (BM25 + FAISS)**
- Título: "1. Recuperación — BM25 + FAISS"
- 5 mini-cards mostrando los chunks recuperados
- Cada card: nombre del libro (truncado), página, texto preview (2 líneas), barra de score FAISS animada
- Las barras se animan de 0 a su valor real con `transition: width 0.6s ease`

**Paso 2 — Reranker**
- Título: "2. Reranker — Cross-Encoder mMARCO"
- Los mismos 5 chunks reordenados según score del reranker
- La reordenación se anima visualmente (las cards se mueven)
- Barras actualizadas con scores del cross-encoder
- Chunks con score bajo (< -3.0) se atenúan con `opacity: 0.35`

**Paso 3 — Contexto final**
- Título: "3. Contexto enviado al LLM"
- Los chunks que superaron el threshold aparecen con `border: 1px solid var(--border-em)`
- Los descartados aparecen con texto tachado y color `var(--text-4)`

### UI
- Fondo `rgba(255,255,255,0.02)`, bordes `var(--border)`
- Scores en fuente `JetBrains Mono` (ya disponible en el proyecto)
- Nombres de libros con ícono `book-open` de Lucide
- El panel puede colapsarse de nuevo con click en el mismo botón

---

## Orden de implementación sugerido

1. TTS — más simple, impacto inmediato en demo
2. Perfil clínico modal — independiente, no afecta otros features
3. Visualización pipeline RAG — datos ya disponibles, solo UI
4. Cuerpo humano SVG — más complejo (SVG + drawer + integración)

## Qué NO cambia

- Ningún archivo Python
- Ningún endpoint de la API
- La lógica de RAG, reranker ni agente ReAct
- El sistema de sesiones SQLite
- Tests existentes
