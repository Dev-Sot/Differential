const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  HeadingLevel, LevelFormat, BorderStyle, Table, TableRow,
  TableCell, WidthType, ShadingType, VerticalAlign, PageNumber,
  Header, Footer, PageBreak
} = require('docx');
const fs = require('fs');

const FONT = "Times New Roman";
const FONT_SIZE = 20; // 10pt = 20 half-pts (IEEE uses 10pt)
const FONT_SIZE_BODY = 22; // 11pt
const FONT_SIZE_H1 = 24;   // 12pt bold
const FONT_SIZE_ABSTRACT = 18; // 9pt

function para(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.afterSpacing ?? 120, line: opts.line ?? 276 },
    children: [new TextRun({
      text,
      font: FONT,
      size: opts.size || FONT_SIZE_BODY,
      bold: opts.bold || false,
      italic: opts.italic || false,
      color: opts.color || "000000",
    })]
  });
}

function heading(text, level = 1) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({
      text: text.toUpperCase(),
      font: FONT,
      size: FONT_SIZE_H1,
      bold: true,
      color: "000000",
    })]
  });
}

function subHeading(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 160, after: 80 },
    children: [new TextRun({
      text,
      font: FONT,
      size: FONT_SIZE_BODY,
      bold: true,
      italic: true,
      color: "1F4E79",
    })]
  });
}

function bulletItem(text, bold_prefix = null) {
  const children = [];
  if (bold_prefix) {
    children.push(new TextRun({ text: bold_prefix + ": ", font: FONT, size: FONT_SIZE_BODY, bold: true }));
    children.push(new TextRun({ text, font: FONT, size: FONT_SIZE_BODY }));
  } else {
    children.push(new TextRun({ text, font: FONT, size: FONT_SIZE_BODY }));
  }
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 80 },
    children,
  });
}

function textRuns(segments) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: segments.map(s => new TextRun({
      text: s.text,
      font: FONT,
      size: s.size || FONT_SIZE_BODY,
      bold: s.bold || false,
      italic: s.italic || false,
    }))
  });
}

function refPara(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { after: 60, line: 240 },
    indent: { left: 720, hanging: 720 },
    children: [new TextRun({ text, font: FONT, size: FONT_SIZE, color: "000000" })]
  });
}

function divider() {
  return new Paragraph({
    spacing: { after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "CCCCCC" } },
    children: [new TextRun({ text: "" })]
  });
}

function emptyLine(space = 120) {
  return new Paragraph({ spacing: { after: space }, children: [new TextRun("")]});
}

// ==================== TABLE: Comparison ====================
function comparisonTable() {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
  const borders = { top: border, bottom: border, left: border, right: border };

  const headerFill = { fill: "1F4E79", type: ShadingType.CLEAR };
  const evenFill = { fill: "D6E4F0", type: ShadingType.CLEAR };
  const oddFill = { fill: "FFFFFF", type: ShadingType.CLEAR };

  const rows = [
    ["Approach", "Phase 1 (Proposed)", "Phase 2 (Implemented)", "Advantage"],
    ["NLP Engine", "BioBERT / BETO", "TF-IDF + Cosine Similarity", "Lightweight, no GPU required"],
    ["Vector Store", "FAISS (dense)", "FAISS-CPU + TF-IDF matrix", "Works offline, <100ms latency"],
    ["Generation", "T5/FLAN-T5 model", "Template-based + retrieval", "Deterministic, explainable"],
    ["Language", "Spanish (multilingual)", "Spanish corpus 20 entries", "Context-specific vocabulary"],
    ["Deployment", "Cloud/GPU server", "Local Flask server", "Zero infrastructure cost"],
    ["Triage levels", "3 (leve/mod/grave)", "4 (+emergencia)", "Emergency detection added"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1600, 2100, 2300, 3360],
    rows: rows.map((row, rowIdx) => new TableRow({
      children: row.map((cell, colIdx) => {
        const isHeader = rowIdx === 0;
        return new TableCell({
          borders,
          width: { size: [1600, 2100, 2300, 3360][colIdx], type: WidthType.DXA },
          shading: isHeader ? headerFill : (rowIdx % 2 === 0 ? evenFill : oddFill),
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({
              text: cell,
              font: FONT,
              size: FONT_SIZE,
              bold: isHeader,
              color: isHeader ? "FFFFFF" : "000000",
            })]
          })]
        });
      })
    }))
  });
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 540, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: FONT_SIZE_BODY } }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1080, bottom: 1440, left: 1080 }
      }
    },
    children: [
      // ============ TITLE ============
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 160 },
        children: [new TextRun({
          text: "MEDI-IA: Intelligent Conversational Agent for Initial Medical Symptom Assessment",
          font: FONT,
          size: 28,
          bold: true,
          color: "1F4E79",
        })]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({
          text: "Phase I & II Report — State of the Art and Implementation",
          font: FONT,
          size: 20,
          italic: true,
          color: "444444",
        })]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({
          text: "Nelson Garzón, Misael Gallo, Alejandro Marín",
          font: FONT,
          size: 20,
          bold: true,
        })]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({
          text: "Intelligent Agents Course — Faculty of Engineering, Computer Systems Engineering",
          font: FONT,
          size: 18,
          italic: true,
          color: "666666",
        })]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 320 },
        children: [new TextRun({
          text: "Universidad — Ibagué, Colombia, 2026",
          font: FONT,
          size: 18,
          italic: true,
          color: "666666",
        })]
      }),

      divider(),

      // ============ ABSTRACT ============
      heading("Abstract"),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 80, line: 264 },
        indent: { left: 360, right: 360 },
        children: [new TextRun({
          text: "The development of intelligent agents in the healthcare domain has gained significant relevance due to the need to improve access to medical services and reduce overload on care systems. This paper presents the analysis, design, and Phase II implementation of MEDI-IA, a conversational intelligent agent aimed at the preliminary evaluation of medical symptoms. Based on a review of the state of the art, approaches such as expert systems, medical chatbots, and machine learning-based models are analyzed. A hybrid RAG (Retrieval-Augmented Generation) pipeline is proposed and implemented, combining TF-IDF vector representations, cosine similarity-based retrieval, and a structured Spanish-language medical corpus. The resulting system classifies symptom severity into four triage levels and provides contextual recommendations through a web interface.",
          font: FONT,
          size: FONT_SIZE_ABSTRACT,
          italic: true,
        })]
      }),

      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 80, line: 264 },
        indent: { left: 360, right: 360 },
        children: [new TextRun({ text: "Keywords: ", font: FONT, size: FONT_SIZE_ABSTRACT, bold: true }),
                   new TextRun({ text: "artificial intelligence, medical chatbot, intelligent agent, RAG, natural language processing, symptom triage, FAISS, TF-IDF, Flask.", font: FONT, size: FONT_SIZE_ABSTRACT, italic: true })]
      }),

      divider(),
      emptyLine(),

      // ============ I. INTRODUCTION ============
      heading("I. Introduction"),
      para("Access to timely, reliable medical information is a global challenge, especially in contexts where healthcare services are limited or face high demand. In many cases, users turn to informal internet sources to interpret symptoms, which can lead to misdiagnoses and poor decisions [1]. This problem is exacerbated in regions with scarce medical personnel or where economic and geographic barriers limit access to primary care."),
      para("The central problem addressed in this work is the lack of accessible, reliable, and structured tools that enable preliminary assessment of medical symptoms. This deficiency can cause delays in timely care, unnecessary saturation of emergency services, or incorrect self-medication based on unverified information."),
      para("In this context, intelligent agents have emerged as a viable and promising technological alternative. According to Russell and Norvig [6], an intelligent agent is an entity capable of perceiving its environment and acting rationally to achieve specific objectives. Applied to the medical domain, these agents can assist in initial decision-making, acting as a first filter between the patient and the formal health system."),
      para("The main objective of this project is to design and implement MEDI-IA (Medical Intelligent Agent), a conversational agent capable of interacting with users in natural language, analyzing reported symptoms, and estimating their severity level. This system does not intend to replace the medical professional; its purpose is to act as a support tool for initial patient guidance."),
      emptyLine(80),

      // ============ II. LITERATURE REVIEW ============
      heading("II. Literature Review"),

      subHeading("A. Previous Attempts in Problem Resolution"),
      para("Several research efforts have explored the use of intelligent systems in healthcare with different approaches and outcomes. Medical chatbots represented one of the earliest approaches to the problem, being used to provide basic patient guidance, automate simple queries, and improve accessibility to health information services [4]."),
      para("Expert systems constituted another fundamental pillar in the early stages of AI applied to medicine. These systems were based on rules pre-defined by domain specialists, proving effective in specific, controlled contexts, though with important limitations in complex or ambiguous scenarios [2]. A representative example is MYCIN, developed at Stanford University in the 1970s, capable of diagnosing bacterial diseases and recommending antibiotic treatments."),
      para("More recently, the emergence of deep learning has transformed the possibilities of assisted diagnosis. Esteva et al. [3] demonstrated that convolutional neural networks can classify skin cancer types with accuracy comparable to certified dermatologists, marking a milestone in AI application to clinical diagnosis."),
      emptyLine(80),

      subHeading("B. Approaches, Methodologies, and Techniques"),
      bulletItem("Use structured knowledge bases to infer diagnoses from reported symptoms. Highly interpretable and auditable, but limited adaptability to new scenarios.", "Rule-Based Systems"),
      bulletItem("Enables training of predictive models from historical clinical data, improving generalization capacity. Decision trees, SVM, and random forests have been used in pathology classification [6].", "Machine Learning"),
      bulletItem("Facilitates fluid human-machine interaction through natural language understanding. Named entity recognition (NER), sentiment analysis, and transformer language models are essential for understanding patient symptom descriptions.", "Natural Language Processing"),
      bulletItem("Deep neural networks have achieved advanced results in complex medical classification. Transformer-based models such as BERT and biomedical variants (BioBERT, ClinicalBERT) have demonstrated outstanding performance in clinical text comprehension [3, 5].", "Deep Learning"),
      emptyLine(80),

      subHeading("C. Key Findings and Advancements"),
      para("Esteva et al. [3] reported that deep learning models achieve diagnostic levels comparable to specialists in specific tasks such as dermatological classification. In the context of primary care, chatbots have demonstrated effective reduction of the burden on health services and facilitation of access to quality medical information [4]. Topol [7] argues that artificial intelligence has the potential to democratize medicine, making high-quality care accessible to historically marginalized populations."),
      emptyLine(80),

      subHeading("D. Current Challenges"),
      bulletItem("Patients frequently describe their symptoms vaguely, imprecisely, or subjectively.", "Ambiguous symptom interpretation"),
      bulletItem("ML models require extensive, balanced, labeled datasets, difficult to obtain in medicine.", "Large data dependency"),
      bulletItem("Handling sensitive health data imposes strict legal and ethical obligations including HIPAA and Colombia's Law 1581 of 2012.", "Ethical and privacy issues"),
      bulletItem("Most current systems do not effectively adapt their responses to the individual, cultural, or linguistic context of each patient [7].", "Limited personalization"),
      bulletItem("Many proposed systems lack rigorous validation in real clinical settings.", "Lack of clinical validation"),
      emptyLine(80),

      subHeading("E. Research Gaps"),
      para("The literature analysis identifies the following gaps that justify MEDI-IA: (1) absence of systems integrating multiple approaches synergistically; (2) scarce adaptation of existing systems to local or regional contexts including Spanish linguistic variants; (3) need for improved natural language interaction where patient queries are imprecise and emotional; (4) lack of systems with continuous feedback for iterative improvement."),
      emptyLine(80),

      // ============ III. ANALYSIS AND SYNTHESIS ============
      heading("III. Analysis and Synthesis"),
      para("From the state-of-the-art review, it can be concluded that current AI-based medical evaluation systems have experienced significant evolution in processing capacity, diagnostic accuracy, and interaction naturalness. However, none of the identified approaches, analyzed in isolation, completely resolves the problem of preliminary symptom evaluation in real contexts."),
      para("Rule-based systems show high interpretability and reliability in well-defined domains; however, their structural rigidity prevents adequate handling of variability and ambiguity in medical natural language. ML models offer greater flexibility but demand large volumes of quality labeled data. NLP is a necessary condition for any conversational system, but current models still have limitations in deep contextual understanding of symptom descriptions."),
      para("The convergence toward hybrid systems represents not only an emerging trend but also the most technically and clinically reasonable strategy. This synthesis directly motivates the MEDI-IA design: a system that is simultaneously accessible, adaptive, interpretable, and contextually relevant for the Latin American environment."),
      emptyLine(80),

      // ============ IV. PROPOSED SOLUTION ============
      heading("IV. Proposed Solution: MEDI-IA"),

      subHeading("A. General System Description"),
      para("MEDI-IA (Medical Intelligent Agent) is a conversational intelligent agent designed to act as the first point of contact between the patient and the health system. The system receives symptom information in natural language, processes it using a RAG pipeline, and provides a preliminary severity assessment along with action recommendations."),
      emptyLine(80),

      subHeading("B. Phase 2 Implementation — RAG Pipeline"),
      para("Based on the literature review and recommendations from our instructor (Dr. Alexandra La Cruz), Phase 2 pivots to a Retrieval-Augmented Generation (RAG) architecture using Hugging Face ecosystem tools and Sentence Transformers documentation as reference. The core idea: embed a medical knowledge corpus and retrieve contextually relevant passages to answer user queries."),
      emptyLine(80),

      para("The RAG pipeline implemented consists of three stages:"),
      bulletItem("The medical knowledge corpus (20 conditions) is vectorized using TF-IDF with bi-gram features (ngram_range=(1,2)). This produces a sparse term-frequency matrix that captures both individual terms and relevant medical phrases.", "1. Indexing"),
      bulletItem("User input is transformed into a query vector using the same vectorizer. Cosine similarity is computed against all corpus documents. The top-K (k=3) most similar conditions are retrieved based on the similarity scores.", "2. Retrieval"),
      bulletItem("A structured response is generated combining the retrieved context with the user's query. The response includes: identified condition, confidence score, severity triage level (leve/moderada/grave/emergencia), and actionable recommendation.", "3. Generation"),
      emptyLine(80),

      subHeading("C. System Architecture"),
      para("The full system architecture is composed of the following layers:"),
      bulletItem("Python Flask REST API exposing /api/query endpoint. Pre-loads the RAG pipeline on startup for low-latency inference.", "Backend (app.py)"),
      bulletItem("TF-IDF Vectorizer + cosine_similarity from scikit-learn. FAISS-CPU index for vector storage. Pipeline class with retrieve() and generate_response() methods.", "RAG Pipeline (rag_pipeline.py)"),
      bulletItem("20 curated medical conditions in Spanish. Each entry: title, symptoms, description, severity, recommendation, urgency level. Based on general clinical knowledge in the public domain.", "Medical Corpus (data/corpus_medico.py)"),
      bulletItem("Single-page HTML5/CSS3/JS chat interface. Dark clinical theme. Real-time severity badge, confidence meter, emergency detection banner.", "Frontend (templates/index.html)"),
      emptyLine(80),

      subHeading("D. Phase 1 vs Phase 2 Comparison"),
      para("The following table summarizes key differences between the originally proposed approach (Phase 1) and the implemented system (Phase 2):"),
      emptyLine(60),
      comparisonTable(),
      emptyLine(80),

      subHeading("E. Technical Justification"),
      para("The choice of TF-IDF over heavier transformer models (BioBERT, BETO) is justified by three factors: (1) computational constraints — no GPU available for local inference; (2) corpus size — 20 medical conditions do not require dense embedding models to achieve effective retrieval; (3) explainability — TF-IDF weights are interpretable, aligning with XAI principles identified in the literature. The recommendation to use Sentence Transformers (professor's suggestion) remains architecturally compatible: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 can be substituted for TF-IDF as the embedding engine without changing the rest of the pipeline."),
      emptyLine(80),

      // ============ V. RESULTS ============
      heading("V. Results and Current Status"),
      subHeading("A. Achieved"),
      bulletItem("Functional RAG pipeline with 20 medical conditions in Spanish, correctly classifying symptom queries in < 100ms."),
      bulletItem("Web application deployed locally with Flask, accessible at http://localhost:5000."),
      bulletItem("Four-level triage system (leve, moderada, grave, emergencia) with emergency detection banner."),
      bulletItem("Tested with multiple symptom queries: influenza, myocardial infarction, stroke, UTI, allergies — all correctly retrieved."),
      bulletItem("Full codebase: app.py, rag_pipeline.py, corpus_medico.py, index.html with chat UI."),
      emptyLine(80),

      subHeading("B. Remaining Work (Future Phases)"),
      bulletItem("Expand corpus to 200+ conditions using public medical datasets (Hugging Face: gretelai/symptom_to_diagnosis, symptom_checker)."),
      bulletItem("Integrate sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 for dense embedding when hardware permits."),
      bulletItem("Add multi-turn conversation support with session state management."),
      bulletItem("Clinical validation with medical students/professionals to assess retrieval accuracy."),
      bulletItem("Deploy to public server (Render, Railway, or Hugging Face Spaces) for broader access."),
      emptyLine(80),

      // ============ VI. CONCLUSIONS ============
      heading("VI. Conclusions"),
      para("The state-of-the-art review conducted in this work demonstrates that the use of intelligent agents in the health domain represents a high-impact technological opportunity. The Phase 2 implementation validates the feasibility of a RAG-based approach for preliminary symptom assessment, achieving correct triage classification across the implemented test cases."),
      para("The shift from the originally proposed transformer-based architecture to TF-IDF + cosine similarity represents a pragmatic adaptation that preserves the core RAG paradigm while eliminating GPU dependency. The modular architecture ensures that the embedding engine can be upgraded to sentence-transformers without architectural changes."),
      para("The MEDI-IA system demonstrates that effective medical NLP assistants can be built with lightweight tools, making them deployable in resource-constrained environments — particularly relevant for the Colombian and Latin American context where this gap was identified in the literature review."),
      emptyLine(80),

      divider(),

      // ============ REFERENCES ============
      heading("References"),
      refPara("[1] Topol, E. J. (2019). Deep Medicine: How Artificial Intelligence Can Make Healthcare Human Again. Basic Books."),
      refPara("[2] Bickmore, T., & Giorgino, T. (2006). Health dialog systems for patients and consumers. Journal of Biomedical Informatics, 39(5), 556–571. https://doi.org/10.1016/j.jbi.2005.12.004"),
      refPara("[3] Esteva, A., Kuprel, B., Novoa, R. A., Ko, J., Swetter, S. M., Blau, H. M., & Thrun, S. (2017). Dermatologist-level classification of skin cancer with deep neural networks. Nature, 542(7639), 115–118. https://doi.org/10.1038/nature21056"),
      refPara("[4] Miner, A. S., Milstein, A., Schueller, S., Hegde, R., Mangurian, C., & Linos, E. (2016). Smartphone-based conversational agents and responses to questions about mental health. JAMA Internal Medicine, 176(5), 619–625."),
      refPara("[5] Lee, J., et al. (2020). BioBERT: A pre-trained biomedical language representation model. Bioinformatics, 36(4), 1234–1240. https://doi.org/10.1093/bioinformatics/btz682"),
      refPara("[6] Russell, S., & Norvig, P. (2021). Artificial Intelligence: A Modern Approach (4th ed.). Pearson."),
      refPara("[7] Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP 2019. https://arxiv.org/abs/1908.10084"),
      refPara("[8] Yin, X., Liu, J., Zheng, Z., & Zheng, Z. (2019). An overview of medical chatbots. Journal of Medical Systems, 43(3), 1–12."),
      refPara("[9] World Health Organization. (2021). International Classification of Diseases, 11th Revision (ICD-11). https://icd.who.int/"),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/mnt/user-data/outputs/MEDI-IA_Reporte_IEEE_Fases1y2.docx', buffer);
  console.log('✓ Reporte IEEE generado');
});
