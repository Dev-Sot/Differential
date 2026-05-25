"""
Evaluacion completa del pipeline RAG MEDI-IA contra el dataset anotado.

Metricas calculadas:
  - Recall@k (k=1,3,5): fraccion de queries donde el libro correcto aparece en top-k
  - MRR (Mean Reciprocal Rank): 1/rango del primer resultado relevante, promediado
  - Precision@5: fraccion de los 5 resultados que provienen de libros relevantes
  - Guardrails accuracy: fraccion de consultas no-medicas correctamente rechazadas
  - Mejora reranker: % de queries donde el reranker cambio el top-1 frente a FAISS

Uso:
  venv/Scripts/python.exe -m src.evaluation_full
  make eval-full
"""

import os
import json
import time
import csv
from datetime import datetime

from src.rag.retriever import retrieve
from src.rag.reranker import rerank
from src.guardrails import is_medical_query

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH  = os.path.join(BASE_DIR, "data", "eval_dataset.json")
RESULTS_PATH  = os.path.join(BASE_DIR, "data", "eval_full_results.json")
CSV_PATH      = os.path.join(BASE_DIR, "data", "eval_full_results.csv")

BOOK_MAP = {
    "Harrison":    "Harrison Principios De Medicina Interna 19 1",
    "Oxford":      "Oxford Handbook of Clinical Medicine 10th Edition",
    "Symptoms":    "Symptoms to diagnosis ",
    "Top100":      "The Top 100 Drugs Clinical",
    "Tintinalli":  "TintinalliEmergencyMedicineManual",
    "Adams":       "adams-and-victors-principles-of-neurology-8th",
    "Harrison_ID": "HARRISONS-INFECTIOUS-DISEASE",
    "Infectious":  "InfectiousDiseasesA_ClinicalShortCourse",
    "Robbins":     "compendio-de-robbins-y-cotran-patologia",
    "Nelson":      "Nelson Textbook of Pediatrics",
    "Kaplan":      "Kaplan-Sadock_Pocket Handbook of Clinical Psychiatry",
    "Williams":    "Williams Obstetrics",
    "Lange":       "40medicalbooksstore_2017_lange_case",
    "ABC_Derm":    "ABC-of-Dermatology-ABC-Series",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_dataset() -> dict:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def _chunk_is_relevant(chunk: dict, expected_books: list[str]) -> bool:
    book = chunk.get("book", "")
    return any(BOOK_MAP.get(short, short) in book for short in expected_books)


def _first_relevant_rank(chunks: list[dict], expected_books: list[str]) -> int | None:
    for i, c in enumerate(chunks, 1):
        if _chunk_is_relevant(c, expected_books):
            return i
    return None


# ── Evaluacion por query ──────────────────────────────────────────────────────

def _evaluate_guardrail(item: dict) -> dict:
    rejected = not is_medical_query(item["query"])
    return {
        "id":                item["id"],
        "categoria":         item["categoria"],
        "query":             item["query"],
        "es_medica":         False,
        "guardrail_correct": rejected,
        "recall_1":          None,
        "recall_3":          None,
        "recall_5":          None,
        "mrr":               None,
        "precision_5":       None,
        "top1_changed":      None,
        "faiss_top1_libro":  None,
        "rerank_top1_libro": None,
        "primer_rango_relevante": None,
    }


def _evaluate_medical(item: dict) -> dict:
    q        = item["query"]
    expected = item.get("libros_relevantes", [])

    faiss_candidates = retrieve(q, top_k=20)
    reranked         = rerank(q, faiss_candidates, top_k=5) if faiss_candidates else []

    faiss_top1  = faiss_candidates[0] if faiss_candidates else {}
    rerank_top1 = reranked[0]         if reranked         else {}

    faiss_top1_libro  = faiss_top1.get("book",  "")
    rerank_top1_libro = rerank_top1.get("book", "")

    rank = _first_relevant_rank(reranked, expected)
    r1 = any(_chunk_is_relevant(c, expected) for c in reranked[:1])
    r3 = any(_chunk_is_relevant(c, expected) for c in reranked[:3])
    r5 = any(_chunk_is_relevant(c, expected) for c in reranked[:5])

    relevant_count = sum(1 for c in reranked if _chunk_is_relevant(c, expected))
    p5 = relevant_count / max(len(reranked), 1)

    return {
        "id":                      item["id"],
        "categoria":               item["categoria"],
        "subcategoria":            item.get("subcategoria", ""),
        "query":                   q,
        "gravedad_esperada":       item.get("gravedad_esperada", ""),
        "dificultad":              item.get("dificultad", ""),
        "es_medica":               True,
        "guardrail_correct":       True,
        "libros_esperados":        expected,
        "faiss_top1_libro":        faiss_top1_libro,
        "rerank_top1_libro":       rerank_top1_libro,
        "top1_changed":            faiss_top1_libro != rerank_top1_libro,
        "primer_rango_relevante":  rank,
        "recall_1":                r1,
        "recall_3":                r3,
        "recall_5":                r5,
        "mrr":                     round(1.0 / rank if rank else 0.0, 4),
        "precision_5":             round(p5, 4),
    }


# ── Metricas agregadas ────────────────────────────────────────────────────────

def _compute_metrics(results: list[dict]) -> dict:
    medical    = [r for r in results if r["es_medica"]]
    guardrails = [r for r in results if not r["es_medica"]]

    n = len(medical)
    if n == 0:
        return {}

    recall_1    = sum(r["recall_1"]    for r in medical) / n
    recall_3    = sum(r["recall_3"]    for r in medical) / n
    recall_5    = sum(r["recall_5"]    for r in medical) / n
    mrr         = sum(r["mrr"]         for r in medical) / n
    precision_5 = sum(r["precision_5"] for r in medical) / n
    top1_changed = sum(1 for r in medical if r.get("top1_changed"))
    guardrail_ok = sum(r["guardrail_correct"] for r in guardrails)

    # Por categoria
    cats: dict[str, list] = {}
    for r in medical:
        cats.setdefault(r["categoria"], []).append(r)

    by_category = {}
    for cat, items in cats.items():
        ni = len(items)
        by_category[cat] = {
            "n":        ni,
            "recall_1": round(sum(r["recall_1"] for r in items) / ni, 3),
            "recall_3": round(sum(r["recall_3"] for r in items) / ni, 3),
            "recall_5": round(sum(r["recall_5"] for r in items) / ni, 3),
            "mrr":      round(sum(r["mrr"]       for r in items) / ni, 3),
        }

    # Por dificultad
    diffs: dict[str, list] = {}
    for r in medical:
        diffs.setdefault(r.get("dificultad", "?"), []).append(r)

    by_difficulty = {}
    for diff, items in diffs.items():
        nd = len(items)
        by_difficulty[diff] = {
            "n":        nd,
            "recall_5": round(sum(r["recall_5"] for r in items) / nd, 3),
            "mrr":      round(sum(r["mrr"]       for r in items) / nd, 3),
        }

    return {
        "queries_medicas":          n,
        "queries_guardrails":       len(guardrails),
        "recall_at_1":              round(recall_1,    4),
        "recall_at_3":              round(recall_3,    4),
        "recall_at_5":              round(recall_5,    4),
        "mrr":                      round(mrr,         4),
        "precision_at_5":           round(precision_5, 4),
        "top1_changed_by_reranker": f"{top1_changed}/{n}",
        "top1_changed_pct":         round(top1_changed / n, 4),
        "guardrail_accuracy":       round(guardrail_ok / max(len(guardrails), 1), 4),
        "guardrail_correct":        f"{guardrail_ok}/{len(guardrails)}",
        "by_category":              by_category,
        "by_difficulty":            by_difficulty,
    }


# ── Runner principal ──────────────────────────────────────────────────────────

def run_full_evaluation(verbose: bool = True) -> dict:
    dataset = _load_dataset()
    queries = dataset["queries"]
    total   = len(queries)

    if verbose:
        print(f"\n  Cargando dataset: {total} queries "
              f"({dataset['meta']['queries_medicas']} medicas + "
              f"{dataset['meta']['queries_guardrails']} guardrails)")
        print("  Iniciando evaluacion...\n")

    t0 = time.monotonic()
    results = []

    for i, item in enumerate(queries, 1):
        if verbose:
            tag = "MED" if item["es_medica"] else "GRD"
            print(f"  [{i:02d}/{total}] [{tag}] {item['id']} — {item['query'][:65]}...")

        if item["es_medica"]:
            result = _evaluate_medical(item)
        else:
            result = _evaluate_guardrail(item)

        results.append(result)

    elapsed = round(time.monotonic() - t0, 1)
    metrics = _compute_metrics(results)

    return {
        "timestamp":       datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_s":      elapsed,
        "dataset_version": dataset["meta"]["version"],
        "config": {
            "faiss_top_k":   20,
            "reranker_top_k": 5,
            "min_score_faiss": 0.20,
        },
        "metrics": metrics,
        "results": results,
    }


# ── Reporte en consola ────────────────────────────────────────────────────────

def print_report(data: dict) -> None:
    m   = data["metrics"]
    sep = "=" * 60

    CAT_LABELS = {
        "sintomas_diagnostico": "Sintomas -> Diagnostico",
        "urgencias_triaje":     "Urgencias y Triaje",
        "farmacologia":         "Farmacologia",
        "fisiopatologia":       "Fisiopatologia",
    }

    print(f"\n{sep}")
    print("  MEDI-IA -- Evaluacion Completa del Pipeline RAG")
    print(f"  Dataset v{data['dataset_version']}  |  {data['timestamp'][:10]}")
    print(f"  {m['queries_medicas']} queries medicas  +  {m['queries_guardrails']} guardrails")
    print(f"  Config: FAISS top-{data['config']['faiss_top_k']} -> Reranker top-{data['config']['reranker_top_k']}")
    print(sep)

    print("\n  METRICAS GLOBALES")
    print(f"  {'Recall@1':<20}: {m['recall_at_1']*100:6.1f}%   (libro correcto en el #1)")
    print(f"  {'Recall@3':<20}: {m['recall_at_3']*100:6.1f}%   (libro correcto en top-3)")
    print(f"  {'Recall@5':<20}: {m['recall_at_5']*100:6.1f}%   (libro correcto en top-5)")
    print(f"  {'MRR':<20}: {m['mrr']:6.4f}   (rango reciproco medio)")
    print(f"  {'Precision@5':<20}: {m['precision_at_5']*100:6.1f}%   (fragmentos relevantes en top-5)")
    print(f"  {'Guardrails':<20}: {m['guardrail_accuracy']*100:6.1f}%   ({m['guardrail_correct']} consultas no-medicas rechazadas)")
    print(f"  {'Mejora reranker':<20}: {m['top1_changed_pct']*100:6.1f}%   ({m['top1_changed_by_reranker']} queries con top-1 cambiado)")

    print("\n  POR CATEGORIA")
    print(f"  {'Categoria':<28} {'N':>4}  {'R@1':>6}  {'R@3':>6}  {'R@5':>6}  {'MRR':>6}")
    print("  " + "-" * 56)
    for cat, s in m["by_category"].items():
        label = CAT_LABELS.get(cat, cat)
        print(f"  {label:<28} {s['n']:>4}  {s['recall_1']*100:5.0f}%  {s['recall_3']*100:5.0f}%  {s['recall_5']*100:5.0f}%  {s['mrr']:.3f}")

    print("\n  POR DIFICULTAD")
    print(f"  {'Dificultad':<12} {'N':>4}  {'R@5':>6}  {'MRR':>6}")
    print("  " + "-" * 32)
    for diff in ["facil", "medio", "dificil"]:
        if diff in m["by_difficulty"]:
            s = m["by_difficulty"][diff]
            print(f"  {diff:<12} {s['n']:>4}  {s['recall_5']*100:5.0f}%  {s['mrr']:.3f}")

    print(f"\n  Tiempo total: {data['duration_s']}s")
    print(f"{sep}\n")


# ── Guardar resultados ────────────────────────────────────────────────────────

def save_results(data: dict) -> None:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    medical = [r for r in data["results"] if r["es_medica"]]
    fieldnames = [
        "id", "categoria", "subcategoria", "dificultad", "query",
        "libros_esperados", "faiss_top1_libro", "rerank_top1_libro",
        "top1_changed", "primer_rango_relevante",
        "recall_1", "recall_3", "recall_5", "mrr", "precision_5",
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in medical:
            row = dict(r)
            row["libros_esperados"] = ", ".join(r.get("libros_esperados", []))
            row["faiss_top1_libro"]  = row.get("faiss_top1_libro",  "")[:40]
            row["rerank_top1_libro"] = row.get("rerank_top1_libro", "")[:40]
            row["top1_changed"]      = "Si" if r.get("top1_changed") else "No"
            row["recall_1"] = "Si" if r["recall_1"] else "No"
            row["recall_3"] = "Si" if r["recall_3"] else "No"
            row["recall_5"] = "Si" if r["recall_5"] else "No"
            row["mrr"]          = f"{r['mrr']:.4f}"
            row["precision_5"]  = f"{r['precision_5']:.4f}"
            writer.writerow(row)

    print(f"  Resultados guardados:")
    print(f"    JSON completo : {RESULTS_PATH}")
    print(f"    CSV (Excel)   : {CSV_PATH}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    data = run_full_evaluation(verbose=True)
    print_report(data)
    save_results(data)
