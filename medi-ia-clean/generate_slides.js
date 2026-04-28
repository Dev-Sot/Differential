const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = 'MEDI-IA Phase 2 Presentation';

// ============ PALETTE ============
const C = {
  bg_dark:   '060B14',
  bg_card:   '0E1E33',
  bg_mid:    '0A1525',
  accent:    '00D4B8',   // teal
  blue:      '3B82F6',
  text:      'E8F4F8',
  text_sub:  '7CA6C0',
  text_muted:'3D6680',
  white:     'FFFFFF',
  green:     '22C55E',
  yellow:    'F59E0B',
  red:       'EF4444',
  purple:    '8B5CF6',
  border:    '1A3550',
};

const FONT_H = 'Trebuchet MS';
const FONT_B = 'Calibri';

// ============ HELPERS ============
function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.3 };
}

function gridBg(slide) {
  slide.background = { color: C.bg_dark };
  // subtle glow top center
  slide.addShape(pres.shapes.OVAL, {
    x: 2.5, y: -1.5, w: 5, h: 3,
    fill: { color: C.accent, transparency: 92 },
    line: { color: C.bg_dark, width: 0 },
  });
}

function sectionLabel(slide, text) {
  slide.addText(text, {
    x: 0.4, y: 0.18, w: 3, h: 0.22,
    fontSize: 8,
    fontFace: FONT_B,
    color: C.accent,
    charSpacing: 3,
  });
}

function divLine(slide, y) {
  slide.addShape(pres.shapes.LINE, {
    x: 0.4, y, w: 9.2, h: 0,
    line: { color: C.border, width: 0.5 },
  });
}

function footerText(slide) {
  slide.addText('MEDI-IA  ·  Agentes Inteligentes 2026  ·  Universidad', {
    x: 0, y: 5.35, w: 10, h: 0.25,
    fontSize: 7,
    fontFace: FONT_B,
    color: C.text_muted,
    align: 'center',
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: opts.fill || C.bg_card },
    line: { color: opts.border || C.border, width: 0.5 },
    shadow: makeShadow(),
  });
  if (opts.accentLeft) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.04, h,
      fill: { color: opts.accentLeft },
      line: { color: opts.accentLeft, width: 0 },
    });
  }
}

// =====================================================
// SLIDE 1: TITLE
// =====================================================
{
  const sl = pres.addSlide();
  sl.background = { color: C.bg_dark };

  // glow circle
  sl.addShape(pres.shapes.OVAL, {
    x: 3.5, y: -2, w: 6, h: 5,
    fill: { color: C.accent, transparency: 90 },
    line: { color: C.bg_dark, width: 0 },
  });

  // Logo block
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 4.3, y: 0.55, w: 1.4, h: 1.4,
    fill: { color: C.bg_card },
    line: { color: C.accent, width: 1 },
    shadow: { type:"outer", blur:20, offset:0, angle:135, color:C.accent, opacity:0.3 },
  });
  sl.addText('M·IA', {
    x: 4.3, y: 0.55, w: 1.4, h: 1.4,
    fontSize: 20, fontFace: FONT_H, bold: true,
    color: C.accent, align: 'center', valign: 'middle',
  });

  sl.addText('MEDI-IA', {
    x: 0.5, y: 2.2, w: 9, h: 0.9,
    fontSize: 44, fontFace: FONT_H, bold: true,
    color: C.white, align: 'center',
    charSpacing: 4,
  });

  sl.addText('Agente Inteligente Conversacional para Evaluación Inicial de Síntomas Médicos', {
    x: 1, y: 3.05, w: 8, h: 0.5,
    fontSize: 14, fontFace: FONT_B,
    color: C.text_sub, align: 'center',
  });

  // Phase badge
  sl.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 3.7, y: 3.7, w: 2.6, h: 0.38,
    fill: { color: C.accent, transparency: 85 },
    line: { color: C.accent, width: 1 },
    rectRadius: 0.05,
  });
  sl.addText('FASE 2  ·  IMPLEMENTACIÓN RAG', {
    x: 3.7, y: 3.7, w: 2.6, h: 0.38,
    fontSize: 8, fontFace: FONT_B, bold: true,
    color: C.accent, align: 'center', valign: 'middle',
    charSpacing: 1,
  });

  sl.addText('Nelson Garzón  ·  Misael Gallo  ·  Alejandro Marín', {
    x: 0.5, y: 4.3, w: 9, h: 0.3,
    fontSize: 11, fontFace: FONT_B,
    color: C.text_muted, align: 'center',
  });

  sl.addText('Agentes Inteligentes · 2026', {
    x: 0.5, y: 4.6, w: 9, h: 0.25,
    fontSize: 9, fontFace: FONT_B, italic: true,
    color: C.text_muted, align: 'center',
  });
}

// =====================================================
// SLIDE 2: PROBLEM + PHASE 1 RECAP
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'CONTEXTO  ·  PROBLEMA');

  sl.addText('¿Qué problema resolvemos?', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true,
    color: C.white,
  });

  divLine(sl, 1.0);

  // Problem card
  card(sl, 0.4, 1.1, 4.4, 1.1, { accentLeft: C.red });
  sl.addText('El problema', {
    x: 0.55, y: 1.15, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: FONT_B, bold: true, color: C.red,
  });
  sl.addText('Falta de herramientas accesibles para evaluar síntomas médicos de forma preliminar. Los usuarios recurren a fuentes no verificadas, generando diagnósticos erróneos y saturación de urgencias.', {
    x: 0.55, y: 1.43, w: 4.1, h: 0.68,
    fontSize: 10, fontFace: FONT_B, color: C.text_sub, lineSpacingMultiple: 1.2,
  });

  // Solution card
  card(sl, 5.1, 1.1, 4.5, 1.1, { accentLeft: C.accent });
  sl.addText('La solución MEDI-IA', {
    x: 5.25, y: 1.15, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: FONT_B, bold: true, color: C.accent,
  });
  sl.addText('Agente conversacional que usa RAG + NLP para recibir síntomas en lenguaje natural, recuperar contexto médico relevante y entregar orientación con nivel de triaje.', {
    x: 5.25, y: 1.43, w: 4.1, h: 0.68,
    fontSize: 10, fontFace: FONT_B, color: C.text_sub, lineSpacingMultiple: 1.2,
  });

  // Phase 1 recap row
  sl.addText('LO QUE PROPUSIMOS EN FASE 1', {
    x: 0.4, y: 2.42, w: 9.2, h: 0.28,
    fontSize: 8, fontFace: FONT_B, bold: true, color: C.text_muted, charSpacing: 2,
  });

  const p1items = [
    { icon: '🧠', label: 'BioBERT / BETO', desc: 'Embeddings NLP' },
    { icon: '🗄️', label: 'FAISS Dense', desc: 'Vector store' },
    { icon: '🔧', label: 'SNOMED CT', desc: 'Knowledge base' },
    { icon: '🌐', label: 'Flask + Vue', desc: 'Interfaz' },
  ];

  p1items.forEach((item, i) => {
    const x = 0.4 + i * 2.35;
    card(sl, x, 2.75, 2.2, 1.55, {});
    sl.addText(item.icon, { x, y: 2.83, w: 2.2, h: 0.4, fontSize: 20, align: 'center' });
    sl.addText(item.label, {
      x, y: 3.25, w: 2.2, h: 0.28,
      fontSize: 10, fontFace: FONT_B, bold: true, color: C.text, align: 'center',
    });
    sl.addText(item.desc, {
      x, y: 3.53, w: 2.2, h: 0.22,
      fontSize: 8.5, fontFace: FONT_B, color: C.text_muted, align: 'center',
    });
  });

  footerText(sl);
}

// =====================================================
// SLIDE 3: PHASE 2 — PIVOT & WHY
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'FASE 2  ·  PIVOTE TÉCNICO');

  sl.addText('¿Por qué cambiamos el enfoque?', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.0);

  sl.addText('La profa recomendó: Hugging Face + Sentence Transformers + "libro médico" en embeddings', {
    x: 0.4, y: 1.06, w: 9.2, h: 0.35,
    fontSize: 11, fontFace: FONT_B, italic: true, color: C.accent,
  });

  const reasons = [
    { icon: '💾', title: 'Sin GPU disponible', body: 'BioBERT requiere >4GB GPU RAM. TF-IDF corre en CPU en < 100ms.', c: C.yellow },
    { icon: '📐', title: 'Corpus pequeño', body: 'Para 20–200 condiciones médicas, TF-IDF es tan efectivo como dense embeddings.', c: C.blue },
    { icon: '🔍', title: 'Explicabilidad (XAI)', body: 'Los pesos TF-IDF son interpretables — requisito clave en sistemas médicos.', c: C.accent },
    { icon: '🔌', title: 'Modular', body: 'El motor de embeddings puede cambiarse a sentence-transformers sin tocar el resto del pipeline.', c: C.green },
  ];

  reasons.forEach((r, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.4 + col * 4.85;
    const y = 1.55 + row * 1.65;
    card(sl, x, y, 4.65, 1.5, { accentLeft: r.c });
    sl.addText(r.icon + '  ' + r.title, {
      x: x + 0.15, y: y + 0.15, w: 4.35, h: 0.32,
      fontSize: 11, fontFace: FONT_B, bold: true, color: r.c,
    });
    sl.addText(r.body, {
      x: x + 0.15, y: y + 0.48, w: 4.35, h: 0.85,
      fontSize: 10, fontFace: FONT_B, color: C.text_sub, lineSpacingMultiple: 1.25,
    });
  });

  footerText(sl);
}

// =====================================================
// SLIDE 4: RAG ARCHITECTURE
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'ARQUITECTURA  ·  RAG PIPELINE');

  sl.addText('Pipeline RAG — Cómo funciona MEDI-IA', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.0);

  // Pipeline stages
  const stages = [
    { num: '01', title: 'Input', desc: 'Usuario describe síntomas en lenguaje natural (español)', icon: '💬', col: C.blue },
    { num: '02', title: 'Vectorize', desc: 'TF-IDF bi-gram transforma el texto en vector sparse', icon: '🔢', col: C.accent },
    { num: '03', title: 'Retrieve', desc: 'Cosine similarity vs. corpus → top-3 condiciones más similares', icon: '🔍', col: C.accent },
    { num: '04', title: 'Generate', desc: 'Respuesta estructurada: condición + triaje + recomendación', icon: '📋', col: C.green },
  ];

  stages.forEach((s, i) => {
    const x = 0.3 + i * 2.4;
    card(sl, x, 1.15, 2.2, 2.9, {});

    sl.addShape(pres.shapes.OVAL, {
      x: x + 0.7, y: 1.28, w: 0.8, h: 0.8,
      fill: { color: s.col, transparency: 80 },
      line: { color: s.col, width: 1 },
    });
    sl.addText(s.num, {
      x: x + 0.7, y: 1.28, w: 0.8, h: 0.8,
      fontSize: 13, fontFace: FONT_H, bold: true,
      color: s.col, align: 'center', valign: 'middle',
    });
    sl.addText(s.icon, {
      x, y: 2.15, w: 2.2, h: 0.4,
      fontSize: 20, align: 'center',
    });
    sl.addText(s.title, {
      x, y: 2.58, w: 2.2, h: 0.32,
      fontSize: 12, fontFace: FONT_H, bold: true,
      color: s.col, align: 'center',
    });
    sl.addText(s.desc, {
      x: x + 0.1, y: 2.92, w: 2.0, h: 0.95,
      fontSize: 9.5, fontFace: FONT_B, color: C.text_sub,
      align: 'center', lineSpacingMultiple: 1.25,
    });

    // Arrow between stages
    if (i < stages.length - 1) {
      sl.addShape(pres.shapes.LINE, {
        x: x + 2.2, y: 2.65, w: 0.2, h: 0,
        line: { color: C.border, width: 1.5 },
      });
    }
  });

  // Corpus box
  card(sl, 0.3, 4.2, 9.4, 0.85, { fill: C.bg_mid, border: C.accent });
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.2, w: 0.05, h: 0.85,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
  sl.addText('📚  CORPUS MÉDICO: ', {
    x: 0.55, y: 4.32, w: 2.2, h: 0.3,
    fontSize: 10, fontFace: FONT_B, bold: true, color: C.accent,
  });
  sl.addText('20 condiciones médicas en español  ·  síntomas, descripción, recomendación, nivel de urgencia  ·  vectorizadas al inicio', {
    x: 2.65, y: 4.32, w: 6.8, h: 0.55,
    fontSize: 9.5, fontFace: FONT_B, color: C.text_sub,
  });

  footerText(sl);
}

// =====================================================
// SLIDE 5: TECH STACK
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'TECNOLOGÍAS  ·  STACK');

  sl.addText('Stack Técnico Implementado', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.0);

  const techs = [
    { layer: 'Frontend', tech: 'HTML5 / CSS3 / JS Vanilla', detail: 'Chat UI · Dark clinical theme · Real-time severity badges · Emergency detection', c: C.blue },
    { layer: 'Backend', tech: 'Python · Flask 3.0', detail: 'REST API · /api/query · Pre-loaded pipeline · JSON responses', c: C.accent },
    { layer: 'RAG Engine', tech: 'scikit-learn · TF-IDF', detail: 'TfidfVectorizer (bigrams) + cosine_similarity · top-k retrieval · < 100ms', c: C.accent },
    { layer: 'Vector Index', tech: 'FAISS-CPU', detail: 'In-memory index · Compatible con dense embeddings (sentence-transformers)', c: C.green },
    { layer: 'NLP Futuro', tech: 'Sentence Transformers', detail: 'paraphrase-multilingual-MiniLM-L12-v2 · Arquitecturalmente compatible · Pendiente GPU', c: C.yellow },
  ];

  techs.forEach((t, i) => {
    const y = 1.12 + i * 0.83;
    card(sl, 0.4, y, 9.2, 0.74, { accentLeft: t.c });
    sl.addText(t.layer, {
      x: 0.65, y: y + 0.06, w: 1.6, h: 0.28,
      fontSize: 9, fontFace: FONT_B, bold: true, color: t.c, charSpacing: 1,
    });
    sl.addText(t.tech, {
      x: 2.35, y: y + 0.05, w: 3.0, h: 0.3,
      fontSize: 11, fontFace: FONT_H, bold: true, color: C.text,
    });
    sl.addText(t.detail, {
      x: 5.45, y: y + 0.07, w: 3.9, h: 0.55,
      fontSize: 9.5, fontFace: FONT_B, color: C.text_sub,
    });
    // divider inside card
    sl.addShape(pres.shapes.LINE, {
      x: 2.3, y: y + 0.12, w: 0, h: 0.48,
      line: { color: C.border, width: 0.5 },
    });
    sl.addShape(pres.shapes.LINE, {
      x: 5.4, y: y + 0.12, w: 0, h: 0.48,
      line: { color: C.border, width: 0.5 },
    });
  });

  footerText(sl);
}

// =====================================================
// SLIDE 6: DEMO RESULTS — TRIAGE LEVELS
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'RESULTADOS  ·  DEMO');

  sl.addText('Sistema de Triaje — 4 Niveles', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.0);

  const levels = [
    {
      level: 'LEVE', icon: '🟢', color: C.green,
      example: '"tengo congestión nasal y estornudos"',
      result: 'Resfriado Común', rec: 'Reposo + hidratación en casa',
    },
    {
      level: 'MODERADA', icon: '🟡', color: C.yellow,
      example: '"fiebre alta, dolor muscular y escalofríos"',
      result: 'Influenza', rec: 'Consultar médico próximos días',
    },
    {
      level: 'GRAVE', icon: '🔴', color: C.red,
      example: '"sed excesiva, visión borrosa, pérdida de peso"',
      result: 'Diabetes (Hiperglucemia)', rec: 'Atención médica pronta',
    },
    {
      level: 'EMERGENCIA', icon: '🚨', color: C.purple,
      example: '"dolor pecho, brazo izquierdo, sudo frío"',
      result: 'Infarto de Miocardio', rec: 'LLAMAR 123 INMEDIATAMENTE',
    },
  ];

  levels.forEach((lv, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.4 + col * 4.85;
    const y = 1.12 + row * 2.0;

    card(sl, x, y, 4.65, 1.82, { accentLeft: lv.color });

    sl.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.15, y: y + 0.14, w: 1.0, h: 0.3,
      fill: { color: lv.color, transparency: 80 },
      line: { color: lv.color, width: 0.5 },
      rectRadius: 0.05,
    });
    sl.addText(lv.icon + ' ' + lv.level, {
      x: x + 0.15, y: y + 0.14, w: 1.0, h: 0.3,
      fontSize: 8, fontFace: FONT_B, bold: true,
      color: lv.color, align: 'center', valign: 'middle',
    });

    sl.addText(lv.example, {
      x: x + 0.15, y: y + 0.52, w: 4.3, h: 0.3,
      fontSize: 9.5, fontFace: FONT_B, italic: true, color: C.text_sub,
    });
    sl.addText('→ ' + lv.result, {
      x: x + 0.15, y: y + 0.84, w: 4.3, h: 0.28,
      fontSize: 11, fontFace: FONT_B, bold: true, color: lv.color,
    });
    sl.addText(lv.rec, {
      x: x + 0.15, y: y + 1.16, w: 4.3, h: 0.5,
      fontSize: 9.5, fontFace: FONT_B, color: C.text_sub,
    });
  });

  footerText(sl);
}

// =====================================================
// SLIDE 7: LOGROS Y TRABAJO FUTURO
// =====================================================
{
  const sl = pres.addSlide();
  gridBg(sl);
  sectionLabel(sl, 'ESTADO ACTUAL  ·  PRÓXIMOS PASOS');

  sl.addText('¿Qué tenemos? ¿Qué falta?', {
    x: 0.4, y: 0.4, w: 9.2, h: 0.55,
    fontSize: 26, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.0);

  // Achieved
  card(sl, 0.4, 1.1, 4.5, 4.0, { border: C.green });
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 1.1, w: 4.5, h: 0.35,
    fill: { color: C.green, transparency: 85 },
    line: { color: C.green, width: 0.5 },
  });
  sl.addText('✅  LOGRADO — FASE 2', {
    x: 0.5, y: 1.1, w: 4.3, h: 0.35,
    fontSize: 10, fontFace: FONT_B, bold: true,
    color: C.green, valign: 'middle', charSpacing: 1,
  });

  const achieved = [
    'Pipeline RAG funcional (TF-IDF + cosine)',
    '20 condiciones médicas en español',
    'App web Flask con chat UI',
    'Triaje en 4 niveles + detección de emergencia',
    'API REST /api/query operativa',
    'Respuestas < 100ms sin GPU',
    'Confianza score e indicador visual',
  ];

  achieved.forEach((a, i) => {
    sl.addText('→  ' + a, {
      x: 0.6, y: 1.55 + i * 0.5, w: 4.1, h: 0.4,
      fontSize: 10, fontFace: FONT_B, color: C.text_sub,
    });
  });

  // Future
  card(sl, 5.1, 1.1, 4.5, 4.0, { border: C.yellow });
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 1.1, w: 4.5, h: 0.35,
    fill: { color: C.yellow, transparency: 85 },
    line: { color: C.yellow, width: 0.5 },
  });
  sl.addText('🔜  TRABAJO FUTURO', {
    x: 5.2, y: 1.1, w: 4.3, h: 0.35,
    fontSize: 10, fontFace: FONT_B, bold: true,
    color: C.yellow, valign: 'middle', charSpacing: 1,
  });

  const future = [
    'Expandir corpus a 200+ condiciones',
    'Integrar sentence-transformers (con GPU)',
    'Conversación multi-turno con estado',
    'Dataset HuggingFace: gretelai/symptom_to_diagnosis',
    'Validación clínica con estudiantes médicos',
    'Deploy en Hugging Face Spaces / Railway',
    'Soporte de voz (speech-to-text)',
  ];

  future.forEach((f, i) => {
    sl.addText('◦  ' + f, {
      x: 5.3, y: 1.55 + i * 0.5, w: 4.1, h: 0.4,
      fontSize: 10, fontFace: FONT_B, color: C.text_sub,
    });
  });

  footerText(sl);
}

// =====================================================
// SLIDE 8: CONCLUSION
// =====================================================
{
  const sl = pres.addSlide();
  sl.background = { color: C.bg_dark };

  sl.addShape(pres.shapes.OVAL, {
    x: -1, y: 1, w: 5, h: 4,
    fill: { color: C.accent, transparency: 94 },
    line: { color: C.bg_dark, width: 0 },
  });

  sl.addText('Conclusiones', {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 30, fontFace: FONT_H, bold: true, color: C.white,
  });

  divLine(sl, 1.1);

  const conclusions = [
    { text: 'MEDI-IA demuestra que un agente médico inteligente puede construirse con herramientas ligeras (TF-IDF + Flask) preservando el paradigma RAG recomendado.', c: C.accent },
    { text: 'El pivote técnico de Fase 1 → Fase 2 fue pragmático y justificado: corpus pequeño + sin GPU = TF-IDF es equivalente a dense embeddings en efectividad.', c: C.blue },
    { text: 'La arquitectura modular garantiza que sentence-transformers puede integrarse sin cambios estructurales cuando haya mayor capacidad computacional.', c: C.green },
    { text: 'El sistema contribuye al vacío identificado en la literatura: herramientas de triaje en español para contexto latinoamericano, accesibles y explicables.', c: C.yellow },
  ];

  conclusions.forEach((c, i) => {
    card(sl, 0.4, 1.25 + i * 0.97, 9.2, 0.82, { accentLeft: c.c });
    sl.addText(c.text, {
      x: 0.6, y: 1.32 + i * 0.97, w: 8.8, h: 0.65,
      fontSize: 10.5, fontFace: FONT_B, color: C.text_sub,
      lineSpacingMultiple: 1.3, valign: 'middle',
    });
  });

  sl.addText('MEDI-IA  ·  Agentes Inteligentes 2026', {
    x: 0, y: 5.3, w: 10, h: 0.3,
    fontSize: 9, fontFace: FONT_B,
    color: C.text_muted, align: 'center',
  });
}

// =====================================================
// WRITE FILE
// =====================================================
pres.writeFile({ fileName: '/mnt/user-data/outputs/MEDI-IA_Presentacion_Fase2.pptx' })
  .then(() => console.log('✓ Presentación generada'))
  .catch(e => console.error('Error:', e));
