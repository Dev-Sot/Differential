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
    "TintinalliEmergencyMedicineManual": [
        (1,   80,  "Resuscitation Techniques"),
        (81,  200, "Cardiovascular Emergencies"),
        (201, 310, "Pulmonary Emergencies"),
        (311, 420, "Neurologic Emergencies"),
        (421, 530, "Gastrointestinal Emergencies"),
        (531, 620, "Renal and Genitourinary Emergencies"),
        (621, 720, "Metabolic and Endocrine Emergencies"),
        (721, 820, "Hematologic and Oncologic Emergencies"),
        (821, 920, "Infectious Diseases"),
        (921, 1000, "Toxicology and Environmental Injuries"),
        (1001, 1089, "Trauma"),
    ],
    "adams-and-victors-principles-of-neurology-8th": [
        (1,   120, "Approach to the Neurological Patient"),
        (121, 350, "Cardinal Manifestations of Neurological Disease"),
        (351, 500, "Growth, Development, and Acquired Diseases of the Nervous System"),
        (501, 700, "Cerebrovascular and Vascular Diseases"),
        (701, 850, "Infections and Inflammatory Diseases"),
        (851, 1000, "Diseases of the Peripheral Nervous System and Muscle"),
        (1001, 1150, "Psychiatric Disorders"),
        (1151, 1300, "Inherited Metabolic and Degenerative Diseases"),
        (1301, 1398, "Neoplastic Disease of the Nervous System"),
    ],
    "HARRISONS-INFECTIOUS-DISEASE": [
        (1,   120, "General Considerations in Infectious Diseases"),
        (121, 380, "Bacterial Infections"),
        (381, 620, "Viral Infections"),
        (621, 800, "Fungal and Parasitic Infections"),
        (801, 1000, "HIV and AIDS"),
        (1001, 1313, "Travel and Environmental Infections"),
    ],
    "InfectiousDiseasesA_ClinicalShortCourse": [
        (1,   50,  "Approach to Infectious Diseases"),
        (51,  120, "Upper and Lower Respiratory Tract Infections"),
        (121, 200, "Cardiovascular and GI Infections"),
        (201, 280, "Urinary Tract and Pelvic Infections"),
        (281, 350, "CNS Infections"),
        (351, 420, "Skin, Soft Tissue, and Bone Infections"),
        (421, 470, "Sexually Transmitted and HIV Infections"),
    ],
    "compendio-de-robbins-y-cotran-patologia-estructural-y-funcional-9a-edicion_booksmedicos.org_": [
        (1,   120, "Patologia General — Lesion y Muerte Celular"),
        (121, 250, "Inflamacion y Reparacion Tisular"),
        (251, 380, "Enfermedades del Sistema Inmune"),
        (381, 500, "Neoplasias"),
        (501, 620, "Enfermedades Geneticas y del Desarrollo"),
        (621, 750, "Patologia de Sistemas — Cardiovascular y Respiratorio"),
        (751, 897, "Patologia de Sistemas — Digestivo, Renal y Endocrino"),
    ],
    "Nelson Textbook of Pediatrics": [
        (1,    400,  "Growth, Development, and General Pediatrics"),
        (401,  800,  "Behavioral and Psychiatric Disorders"),
        (801,  1200, "Neonatal Medicine and Nutrition"),
        (1201, 1800, "Genetics and Immunology"),
        (1801, 2500, "Infectious Diseases"),
        (2501, 3200, "Rheumatic, Pulmonary, and Cardiovascular Diseases"),
        (3201, 4000, "Neurologic and Renal Diseases"),
        (4001, 5041, "Oncology, Endocrinology, and Other Specialties"),
    ],
    "Kaplan-Sadock_Pocket Handbook of Clinical Psychiatry (2019)": [
        (1,   80,  "Classification and Psychiatric Diagnosis"),
        (81,  180, "Anxiety, Trauma, and OCD-Related Disorders"),
        (181, 280, "Mood Disorders"),
        (281, 370, "Schizophrenia and Psychotic Disorders"),
        (371, 460, "Substance-Related and Addictive Disorders"),
        (461, 560, "Child and Adolescent Psychiatry"),
        (561, 660, "Emergency Psychiatry and Consultation"),
        (661, 780, "Psychopharmacology"),
    ],
    "Williams Obstetrics-1376hlm": [
        (1,   150, "Human Pregnancy — Anatomy and Physiology"),
        (151, 400, "Prenatal Care and Assessment"),
        (401, 650, "Labor and Delivery"),
        (651, 850, "Fetal and Neonatal Disorders"),
        (851, 1100, "Obstetric Complications"),
        (1101, 1376, "Medical and Surgical Complications in Pregnancy"),
    ],
    "40medicalbooksstore_2017_lange_case": [
        (1,   120, "Cardiology and Pulmonology Cases"),
        (121, 250, "Gastroenterology and Hepatology Cases"),
        (251, 380, "Neurology and Psychiatry Cases"),
        (381, 500, "Infectious Disease and Rheumatology Cases"),
        (501, 607, "Endocrinology and Nephrology Cases"),
    ],
    "ABC-of-Dermatology-ABC-Series-7th-Edition-compressed": [
        (1,   80,  "Approach to Skin Disease and Examination"),
        (81,  200, "Eczema, Dermatitis, and Psoriasis"),
        (201, 350, "Acne, Rosacea, and Hair Disorders"),
        (351, 500, "Skin Infections — Bacterial, Viral, and Fungal"),
        (501, 650, "Skin Tumors and Pigmented Lesions"),
        (651, 780, "Systemic Diseases with Skin Manifestations"),
        (781, 873, "Special Populations and Topics"),
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
