"""
Corpus médico en español para MEDI-IA.
Basado en información clínica general de dominio público.
Cada entrada tiene: síntomas, condición, nivel de gravedad, recomendación.
"""

CORPUS = [
    {
        "id": 1,
        "titulo": "Resfriado Común (Rinofaringitis aguda)",
        "sintomas": "congestión nasal, estornudos, secreción nasal, dolor de garganta leve, tos seca, malestar general, fiebre leve, pérdida del olfato temporal",
        "descripcion": "El resfriado común es una infección viral del tracto respiratorio superior causada principalmente por rinovirus. Es muy contagioso y se transmite por gotitas respiratorias o contacto con superficies contaminadas.",
        "gravedad": "leve",
        "recomendacion": "Reposo en casa, hidratación abundante, analgésicos de venta libre (paracetamol o ibuprofeno) para aliviar síntomas. Consultar médico si los síntomas persisten más de 10 días o empeoran significativamente.",
        "urgencia": "baja"
    },
    {
        "id": 2,
        "titulo": "Gripe (Influenza)",
        "sintomas": "fiebre alta de aparición súbita, escalofríos, dolor muscular intenso, dolor de cabeza, cansancio extremo, tos seca, dolor de garganta, congestión nasal",
        "descripcion": "La influenza es una infección viral respiratoria causada por el virus influenza A o B. A diferencia del resfriado, la gripe tiene aparición brusca y síntomas más intensos, especialmente fiebre alta y fatiga severa.",
        "gravedad": "moderada",
        "recomendacion": "Reposo absoluto, hidratación abundante, antipiréticos para controlar fiebre. Consultar médico, especialmente en adultos mayores, niños, embarazadas o personas con enfermedades crónicas. Antivirales disponibles en primeras 48 horas.",
        "urgencia": "media"
    },
    {
        "id": 3,
        "titulo": "Gastroenteritis (Infección gastrointestinal)",
        "sintomas": "náuseas, vómitos, diarrea, dolor abdominal, calambres estomacales, fiebre leve, deshidratación, malestar general",
        "descripcion": "La gastroenteritis es la inflamación del estómago e intestinos causada por virus (norovirus, rotavirus), bacterias (Salmonella, E. coli) o parásitos. Es muy común y generalmente autolimitada.",
        "gravedad": "moderada",
        "recomendacion": "Hidratación oral con suero de rehidratación. Dieta blanda (BRAT: plátano, arroz, manzana, tostadas). Consultar médico si hay sangre en heces, fiebre alta, signos graves de deshidratación o síntomas por más de 48 horas.",
        "urgencia": "media"
    },
    {
        "id": 4,
        "titulo": "Migraña",
        "sintomas": "dolor de cabeza pulsátil intenso unilateral, náuseas, vómitos, sensibilidad a la luz, sensibilidad al sonido, aura visual, visión borrosa, mareos",
        "descripcion": "La migraña es un trastorno neurológico crónico caracterizado por episodios recurrentes de cefalea intensa, frecuentemente acompañada de síntomas autonómicos. Puede durar de 4 a 72 horas.",
        "gravedad": "moderada",
        "recomendacion": "Analgésicos (ibuprofeno, paracetamol, triptanes). Reposo en ambiente oscuro y silencioso. Consultar médico para diagnóstico formal y tratamiento preventivo si los episodios son frecuentes.",
        "urgencia": "media"
    },
    {
        "id": 5,
        "titulo": "Hipertensión Arterial",
        "sintomas": "dolor de cabeza occipital, mareos, zumbido en los oídos, visión borrosa, palpitaciones, sangrado nasal, sensación de presión en la cabeza, fatiga",
        "descripcion": "La hipertensión es la elevación persistente de la presión arterial por encima de 140/90 mmHg. Es uno de los principales factores de riesgo cardiovascular y puede ser asintomática durante años.",
        "gravedad": "grave",
        "recomendacion": "Consulta médica urgente para medición de presión arterial. Si la presión es muy alta (>180/120), ir a urgencias. Tratamiento farmacológico, cambios en dieta (reducir sal), ejercicio regular.",
        "urgencia": "alta"
    },
    {
        "id": 6,
        "titulo": "Infección Urinaria (Cistitis)",
        "sintomas": "ardor al orinar, micción frecuente, urgencia urinaria, orina turbia o con mal olor, dolor pélvico, presión en la vejiga, sangre en orina, fiebre leve",
        "descripcion": "La infección urinaria es causada principalmente por bacterias (Escherichia coli) que colonizan el tracto urinario. Es más frecuente en mujeres y puede progresar a infección renal si no se trata.",
        "gravedad": "moderada",
        "recomendacion": "Consulta médica para urocultivo y antibioticoterapia. Hidratación abundante. Si hay fiebre alta, escalofríos o dolor lumbar, acudir a urgencias (puede indicar pielonefritis).",
        "urgencia": "media"
    },
    {
        "id": 7,
        "titulo": "Dolor de Espalda (Lumbalgia)",
        "sintomas": "dolor en la zona lumbar, rigidez muscular, dolor que irradia a piernas, dificultad para moverse, contractura muscular, hormigueo en extremidades, pérdida de sensibilidad",
        "descripcion": "La lumbalgia es el dolor localizado en la parte baja de la espalda. Puede ser de origen muscular, vertebral o neurológico. Es una de las principales causas de discapacidad a nivel mundial.",
        "gravedad": "leve",
        "recomendacion": "Reposo relativo (no absoluto), analgésicos y antiinflamatorios, aplicación de calor local. Si el dolor irradia hacia la pierna con adormecimiento o hay pérdida del control de esfínteres, consultar urgentemente.",
        "urgencia": "baja"
    },
    {
        "id": 8,
        "titulo": "Alergia (Rinitis Alérgica)",
        "sintomas": "estornudos frecuentes, picazón en ojos nariz y garganta, lagrimeo, congestión nasal, secreción nasal clara, ojos rojos e hinchados, erupción cutánea, urticaria",
        "descripcion": "La rinitis alérgica es una inflamación de la mucosa nasal causada por una respuesta inmune exagerada ante alérgenos como polen, polvo, ácaros o pelo de animales.",
        "gravedad": "leve",
        "recomendacion": "Antihistamínicos de venta libre, evitar exposición al alérgeno. Consultar médico para pruebas de alergia y tratamiento preventivo o inmunoterapia en casos severos.",
        "urgencia": "baja"
    },
    {
        "id": 9,
        "titulo": "Diabetes (Síntomas de hiperglucemia)",
        "sintomas": "sed excesiva, orinar con mucha frecuencia, hambre constante, fatiga, visión borrosa, cicatrización lenta, infecciones frecuentes, pérdida de peso sin causa aparente, hormigueo en manos y pies",
        "descripcion": "La diabetes mellitus es un trastorno metabólico crónico caracterizado por niveles elevados de glucosa en sangre, que puede ser de tipo 1 (autoinmune) o tipo 2 (resistencia a la insulina).",
        "gravedad": "grave",
        "recomendacion": "Consulta médica para pruebas de glucemia. Si hay confusión, dificultad para respirar o síntomas graves, acudir a urgencias. Requiere manejo médico especializado, cambios en dieta y posiblemente medicación.",
        "urgencia": "alta"
    },
    {
        "id": 10,
        "titulo": "Ansiedad y Estrés",
        "sintomas": "nerviosismo, sensación de peligro inminente, taquicardia, respiración acelerada, sudoración, temblores, fatiga, dificultad para concentrarse, insomnio, tensión muscular, irritabilidad",
        "descripcion": "El trastorno de ansiedad es una condición mental caracterizada por preocupación excesiva y persistente que interfiere con las actividades diarias. El estrés crónico puede desencadenar o empeorar síntomas físicos.",
        "gravedad": "moderada",
        "recomendacion": "Técnicas de relajación, ejercicio regular, buena higiene del sueño. Consultar con profesional de salud mental. En crisis agudas con síntomas físicos intensos, descartar causas orgánicas.",
        "urgencia": "media"
    },
    {
        "id": 11,
        "titulo": "Ataque al Corazón (Infarto de Miocardio)",
        "sintomas": "dolor opresivo en el pecho que irradia al brazo izquierdo cuello o mandíbula, sudoración fría, náuseas, dificultad para respirar, mareos intensos, sensación de muerte inminente, palidez extrema",
        "descripcion": "El infarto agudo de miocardio ocurre cuando el flujo sanguíneo coronario se obstruye, causando necrosis del tejido cardíaco. Es una emergencia médica que requiere atención inmediata.",
        "gravedad": "grave",
        "recomendacion": "LLAMAR AL 123 O SERVICIO DE EMERGENCIAS INMEDIATAMENTE. No conducir solo al hospital. Si está disponible y no hay alergia, aspirina 300mg. Cada minuto es crítico para salvar tejido cardíaco.",
        "urgencia": "emergencia"
    },
    {
        "id": 12,
        "titulo": "Bronquitis",
        "sintomas": "tos con mucosidad, flema amarilla o verde, dificultad para respirar, silbido al respirar, dolor en el pecho al toser, fatiga, fiebre leve o moderada, garganta irritada",
        "descripcion": "La bronquitis es la inflamación de los bronquios, que puede ser aguda (generalmente viral) o crónica (relacionada con tabaquismo o exposición a irritantes). La tos puede persistir semanas.",
        "gravedad": "moderada",
        "recomendacion": "Reposo, hidratación, humidificador. Broncodilatadores si hay sibilancias. Consultar médico si hay fiebre alta, dificultad respiratoria severa o síntomas por más de 3 semanas (descartar neumonía).",
        "urgencia": "media"
    },
    {
        "id": 13,
        "titulo": "Conjuntivitis",
        "sintomas": "ojos rojos, picazón en los ojos, secreción ocular amarilla o verde, ojos pegados al despertar, lagrimeo excesivo, sensación de arenilla en los ojos, hinchazón de párpados, sensibilidad a la luz",
        "descripcion": "La conjuntivitis es la inflamación de la conjuntiva, la membrana que recubre el ojo. Puede ser viral, bacteriana o alérgica. Es muy contagiosa en su forma infecciosa.",
        "gravedad": "leve",
        "recomendacion": "Limpieza con suero fisiológico, compresas frías. Gotas antibióticas si es bacteriana (prescripción médica). Evitar tocarse los ojos y compartir toallas. Consultar si hay dolor intenso o visión borrosa.",
        "urgencia": "baja"
    },
    {
        "id": 14,
        "titulo": "Dermatitis / Eccema",
        "sintomas": "picazón intensa, piel roja e inflamada, erupción cutánea, piel seca y escamosa, ampollas, costras, piel gruesa y cuarteada, ardor en la piel",
        "descripcion": "La dermatitis es la inflamación de la piel que puede ser de contacto (por sustancias irritantes o alérgenos) o atópica (trastorno crónico relacionado con el sistema inmune).",
        "gravedad": "leve",
        "recomendacion": "Cremas hidratantes, evitar el alérgeno o irritante. Corticosteroides tópicos de baja potencia para brotes. Consultar dermatólogo si es extensa, crónica o si hay signos de infección secundaria.",
        "urgencia": "baja"
    },
    {
        "id": 15,
        "titulo": "Accidente Cerebrovascular (ACV / Ictus)",
        "sintomas": "debilidad súbita en un lado del cuerpo, parálisis facial, dificultad para hablar o entender, visión doble o pérdida de visión, dolor de cabeza súbito intenso, pérdida de equilibrio, confusión repentina",
        "descripcion": "El ACV ocurre cuando el suministro de sangre al cerebro se interrumpe (isquémico) o cuando un vaso sanguíneo se rompe (hemorrágico). Es una emergencia neurológica que requiere tratamiento en los primeros minutos.",
        "gravedad": "grave",
        "recomendacion": "LLAMAR AL 123 INMEDIATAMENTE. Recordar F.A.S.T.: Cara (Face) caída, Brazo (Arm) débil, Habla (Speech) confusa, Tiempo (Time) es crítico. No dar medicamentos. Cada minuto cuenta.",
        "urgencia": "emergencia"
    },
    {
        "id": 16,
        "titulo": "Hipoglucemia (Azúcar baja)",
        "sintomas": "temblores, sudoración, palpitaciones, hambre repentina, mareos, confusión, irritabilidad, palidez, debilidad, visión borrosa, dificultad para concentrarse",
        "descripcion": "La hipoglucemia ocurre cuando el nivel de glucosa en sangre cae por debajo de 70 mg/dL. Es frecuente en diabéticos bajo tratamiento pero puede ocurrir en personas sin diabetes.",
        "gravedad": "moderada",
        "recomendacion": "Consumir inmediatamente 15-20g de carbohidratos de rápida absorción (jugo, azúcar, glucosa). Repetir medición en 15 minutos. Si pierde el conocimiento, llamar emergencias. Consultar médico para ajuste de tratamiento.",
        "urgencia": "alta"
    },
    {
        "id": 17,
        "titulo": "Intoxicación Alimentaria",
        "sintomas": "náuseas intensas, vómitos repetidos, diarrea acuosa o con sangre, cólicos abdominales, fiebre, escalofríos, dolor de cabeza, deshidratación severa",
        "descripcion": "La intoxicación alimentaria es causada por consumir alimentos contaminados con bacterias (Salmonella, Listeria, E. coli), toxinas o parásitos. Los síntomas pueden aparecer entre 30 minutos y varios días.",
        "gravedad": "moderada",
        "recomendacion": "Hidratación con suero oral. Si hay sangre en heces, fiebre alta (>39°C), signos de deshidratación severa, o síntomas por más de 3 días, acudir urgencias. Evitar antiparasitarios sin prescripción.",
        "urgencia": "media"
    },
    {
        "id": 18,
        "titulo": "Asma",
        "sintomas": "silbido al respirar, dificultad para respirar, opresión en el pecho, tos crónica especialmente nocturna, falta de aire al hacer ejercicio, tos con mucosidad, respiración acelerada",
        "descripcion": "El asma es una enfermedad inflamatoria crónica de las vías respiratorias que causa episodios recurrentes de sibilancias, disnea y tos. Los desencadenantes incluyen ejercicio, alérgenos, infecciones y estrés.",
        "gravedad": "moderada",
        "recomendacion": "Usar broncodilatador de rescate (salbutamol). En crisis severa con labios azules o incapacidad para hablar, llamar emergencias. Consultar médico para plan de manejo y medicación preventiva.",
        "urgencia": "alta"
    },
    {
        "id": 19,
        "titulo": "Cálculos Renales (Litiasis renal)",
        "sintomas": "dolor severo en la zona lumbar que irradia a la ingle, náuseas, vómitos, sangre en orina, urgencia urinaria, orina turbia, fiebre si hay infección, dolor cólico intenso",
        "descripcion": "Los cálculos renales son depósitos duros de minerales que se forman en los riñones. El dolor (cólico nefrítico) es uno de los más intensos en medicina, causado por el movimiento del cálculo por el uréter.",
        "gravedad": "grave",
        "recomendacion": "Acudir a urgencias para diagnóstico (ecografía, análisis de orina). Analgesia potente. Hidratación abundante para facilitar expulsión. Litotripcia o cirugía en casos severos.",
        "urgencia": "alta"
    },
    {
        "id": 20,
        "titulo": "Depresión",
        "sintomas": "tristeza persistente, pérdida de interés en actividades, fatiga crónica, cambios en el apetito o peso, insomnio o hipersomnia, dificultad para concentrarse, sentimientos de inutilidad o culpa, pensamientos de muerte",
        "descripcion": "La depresión mayor es un trastorno del estado de ánimo caracterizado por tristeza profunda y persistente que interfiere con la vida diaria. Afecta el bienestar físico, emocional y cognitivo de la persona.",
        "gravedad": "moderada",
        "recomendacion": "Consultar con psicólogo o psiquiatra. No está solo/a. Si hay pensamientos de hacerse daño, contactar línea de crisis o acudir a urgencias. El tratamiento (terapia y/o medicación) es altamente efectivo.",
        "urgencia": "media"
    }
]

GRAVITY_LEVELS = {
    "leve": {
        "color": "#22c55e",
        "icon": "🟢",
        "label": "LEVE",
        "description": "Puede manejarse en casa con cuidados básicos"
    },
    "moderada": {
        "color": "#f59e0b",
        "icon": "🟡",
        "label": "MODERADA",
        "description": "Se recomienda consultar médico en los próximos días"
    },
    "grave": {
        "color": "#ef4444",
        "icon": "🔴",
        "label": "GRAVE",
        "description": "Requiere atención médica pronta"
    },
    "emergencia": {
        "color": "#7c3aed",
        "icon": "🚨",
        "label": "EMERGENCIA",
        "description": "Llame al 123 o acuda a urgencias INMEDIATAMENTE"
    }
}
