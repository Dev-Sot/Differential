"""Generacion de reportes PDF (diagnostico individual y conversacion completa).

Extraido de app.py: son ~300 lineas de formato de documento sin ninguna
dependencia de Flask, asi que viven mejor como modulo propio y testeable
en aislamiento (sin necesidad de un request/response de Flask alrededor).
"""

import re
from datetime import datetime

from fpdf import FPDF

EMERALD = (201, 151, 75)  # brass/gold — acento de marca Differential
BLUE = (59, 130, 246)
SLATE = (71, 85, 105)
MUTED = (148, 163, 184)
DARK = (15, 23, 42)


def _safe(text) -> str:
    """Normaliza texto Unicode a algo representable en las fuentes core del PDF (Latin-1)."""
    replacements = {
        "—": "-", "–": "-",
        "“": '"', "”": '"',
        "‘": "'", "’": "'",
        "…": "...",
    }
    s = str(text or "")
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text or "")
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text


def build_diagnosis_pdf(data: dict) -> bytes:
    """Genera el PDF de un unico reporte de diagnostico (endpoint /api/export/pdf)."""
    gravedad = data.get("gravedad", "moderada")
    sev_fg = {
        "leve":       (22, 163, 74),
        "moderada":   (180, 110, 0),
        "grave":      (185, 28, 28),
        "emergencia": (91, 33, 182),
    }.get(gravedad, (180, 110, 0))
    sev_bg = {
        "leve":       (240, 253, 244),
        "moderada":   (255, 251, 235),
        "grave":      (254, 242, 242),
        "emergencia": (245, 243, 255),
    }.get(gravedad, (255, 251, 235))

    def clean(text):
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text or "")
        skip = [
            "condicion principal", "condicion principal sugerida",
            "nivel de urgencia", "recomendacion",
            "esto no reemplaza", "este reporte",
            "sintomas clave",
        ]
        lines = [
            line for line in text.split("\n")
            if line.strip() and not any(line.strip().lower().startswith(s) for s in skip)
        ]
        return _safe("\n".join(lines).strip())

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    W = pdf.w - 40

    def label(text):
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, text.upper(), ln=True)
        pdf.ln(1)

    def vbar(color, x, y, h):
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 2, h, style="F")

    def hline():
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(4)

    # Header
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*EMERALD)
    pdf.cell(0, 12, "Differential", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.set_y(pdf.get_y() - 9)
    pdf.cell(0, 9, f"Reporte de evaluacion medica  |  {fecha}", align="R", ln=True)
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(1.0)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(8)

    # Query box
    query = _safe(data.get("query", ""))
    if query:
        y0 = pdf.get_y()
        pdf.set_xy(25, y0 + 1)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 4, "CONSULTA DEL PACIENTE", ln=True)
        pdf.set_x(25)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(W - 5, 5.5, query)
        vbar(BLUE, 20, y0, pdf.get_y() - y0)
        pdf.ln(7)

    # Severity pill + condition
    lbl = _safe(data.get("gravedad_label", gravedad.upper()))
    cond = _safe(data.get("condicion_principal", ""))
    pill_w = min(len(lbl) * 2.6 + 10, 45)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*sev_bg)
    pdf.set_text_color(*sev_fg)
    pdf.set_draw_color(*sev_fg)
    pdf.set_line_width(0.4)
    pdf.cell(pill_w, 7, lbl, border=1, fill=True, align="C", ln=False)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK)
    pdf.cell(5, 7, "", ln=False)
    pdf.multi_cell(W - pill_w - 5, 7, cond)
    pdf.ln(7)

    # Analysis
    label("Analisis medico")
    y0 = pdf.get_y()
    pdf.set_xy(25, y0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*SLATE)
    pdf.multi_cell(W - 5, 5.5, clean(data.get("respuesta", "")))
    vbar(EMERALD, 20, y0, pdf.get_y() - y0)
    pdf.ln(7)

    # Recommendation
    label("Recomendacion")
    rec_y = pdf.get_y()
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK)
    pdf.set_fill_color(240, 253, 244)
    pdf.multi_cell(W, 5.5, _safe(data.get("recomendacion", "")), fill=True)
    rec_h = pdf.get_y() - rec_y
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(0.4)
    pdf.rect(20, rec_y, W, rec_h)
    pdf.ln(7)

    # Sources
    fuentes = data.get("fuentes", [])
    if fuentes:
        label("Fuentes bibliograficas")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(W, 5, _safe(", ".join(fuentes)))
        pdf.ln(5)

    # Engine
    label("Motor de IA")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, _safe(data.get("modo", "")), ln=True)
    pdf.ln(7)

    # Disclaimer
    hline()
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(
        W, 5,
        "Differential es una herramienta de practica y no reemplaza la consulta medica profesional. "
        "Este reporte es generado por inteligencia artificial y debe ser validado "
        "por un profesional de la salud calificado. "
        "En caso de emergencia llame al 123 o dirigase a urgencias inmediatamente.",
    )

    return bytes(pdf.output())


def build_conversation_pdf(turns: list) -> bytes:
    """Genera el PDF con todos los turnos de una sesion (endpoint /api/export/conversation)."""
    USER_BG = (219, 234, 254)   # blue-100
    ASST_BG = (209, 250, 229)   # emerald-100

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    W = pdf.w - 40

    # Header
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*EMERALD)
    pdf.cell(0, 12, "Differential", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.set_y(pdf.get_y() - 9)
    pdf.cell(0, 9, f"Historial de sesion  |  {fecha}", align="R", ln=True)
    pdf.set_draw_color(*EMERALD)
    pdf.set_line_width(1.0)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(10)

    for turn in turns:
        role = turn.get("role", "")
        content = _safe(_strip_markdown(turn.get("content", "")))
        if not content.strip():
            continue

        if role == "user":
            bar_color = BLUE
            bg_color = USER_BG
            label_txt = "PACIENTE"
            label_color = BLUE
        else:
            bar_color = EMERALD
            bg_color = ASST_BG
            label_txt = "Differential"
            label_color = (5, 150, 105)

        y0 = pdf.get_y()
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*label_color)
        pdf.set_x(25)
        pdf.cell(0, 4, label_txt, ln=True)
        pdf.ln(1)
        pdf.set_x(25)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*SLATE)
        pdf.set_fill_color(*bg_color)
        pdf.multi_cell(W - 5, 5.2, content, fill=True)
        bar_h = pdf.get_y() - y0
        pdf.set_fill_color(*bar_color)
        pdf.rect(20, y0, 2, bar_h, style="F")
        pdf.ln(6)

    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(
        W, 4.5,
        "Differential es una herramienta de practica y no reemplaza la consulta medica profesional. "
        "Este historial es generado por inteligencia artificial y debe ser validado "
        "por un profesional de la salud. En emergencias llame al 123.",
    )

    return bytes(pdf.output())
