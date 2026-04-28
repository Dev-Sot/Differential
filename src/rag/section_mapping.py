"""
Mapea paginas de los libros a secciones/capitulos conocidos.
Enriquece los chunks con contexto de donde vienen dentro del libro.
"""

SECTION_MAPS: dict[str, list[tuple[int, int, str]]] = {
    "Harrison Principios De Medicina Interna 19 1": [
        (1,   50,  "Introduccion a la Medicina Clinica"),
        (51,  120, "Signos y Sintomas Cardinales"),
        (121, 200, "Dolor - Evaluacion y Manejo"),
        (201, 300, "Enfermedades del Sistema Nervioso"),
        (301, 400, "Enfermedades Infecciosas"),
        (401, 500, "Oncologia y Hematologia"),
        (501, 600, "Enfermedades Cardiovasculares"),
        (601, 700, "Enfermedades Respiratorias"),
        (701, 800, "Enfermedades del Aparato Digestivo"),
        (801, 900, "Enfermedades Reumatologicas"),
        (901, 999, "Endocrinologia y Metabolismo"),
    ],
    "Oxford Handbook of Clinical Medicine 10th Edition": [
        (1,   80,  "Thinking about medicine"),
        (81,  160, "History and examination"),
        (161, 240, "Cardiovascular medicine"),
        (241, 320, "Chest medicine"),
        (321, 400, "Endocrinology"),
        (401, 480, "Gastroenterology"),
        (481, 560, "Renal medicine"),
        (561, 640, "Haematology"),
        (641, 720, "Infectious diseases"),
        (721, 800, "Neurology"),
        (801, 880, "Oncology and palliative care"),
        (881, 999, "Rheumatology"),
    ],
    "Symptoms to diagnosis ": [
        (1,   60,  "Diagnostic Approach"),
        (61,  150, "Chest Pain and Dyspnea"),
        (151, 250, "Abdominal Pain"),
        (251, 350, "Fever and Infectious Symptoms"),
        (351, 450, "Neurological Symptoms"),
        (451, 550, "Musculoskeletal Symptoms"),
        (551, 650, "Urinary and Reproductive Symptoms"),
        (651, 999, "Other Symptoms"),
    ],
    "The Top 100 Drugs Clinical": [
        (1,   100, "Cardiovascular Drugs"),
        (101, 200, "Respiratory and Allergy Drugs"),
        (201, 300, "Gastrointestinal Drugs"),
        (301, 400, "Neurological and Psychiatric Drugs"),
        (401, 500, "Antibiotics and Antiinfectives"),
        (501, 999, "Endocrine, Pain, and Other Drugs"),
    ],
}

DEFAULT_SECTION = "Seccion general"


def get_section(book: str, page: int) -> str:
    """Retorna el nombre de seccion para un libro y pagina dados."""
    ranges = SECTION_MAPS.get(book, [])
    for start, end, section in ranges:
        if start <= page <= end:
            return section
    return DEFAULT_SECTION


def enrich_chunks(chunks: list[dict]) -> list[dict]:
    """Agrega campo 'seccion' a cada chunk."""
    for chunk in chunks:
        chunk["seccion"] = get_section(chunk.get("book", ""), chunk.get("page", 0))
    return chunks
