"""L3 Mastery Gate eval — runs the pipeline TWICE with different seeds, reports
mean ± stdev for faithfulness and context_precision. Asserts:

    faithfulness     >= 0.85   (mean across runs)
    context_precision >= 0.75   (mean across runs)

If both pass, exit 0. Otherwise exit 1 with the failing metric and per-run
breakdown printed for debugging.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

FAITHFULNESS_THRESHOLD = 0.85
CONTEXT_PRECISION_THRESHOLD = 0.75
SEEDS = (7, 42)


def _stdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))


def main() -> int:
    missing = [k for k in ("ANTHROPIC_API_KEY", "COHERE_API_KEY") if not os.environ.get(k)]
    if missing:
        print(f"skip: missing {', '.join(missing)}")
        return 1

    sys.path.insert(0, str(Path(__file__).parent))
    from solution import build_corpus_index, evaluate, load_filings, run_pipeline

    filings_dir = Path(__file__).parent / "data" / "filings"
    if not filings_dir.exists() or not any(filings_dir.glob("*.txt")):
        sys.exit(f"no filings in {filings_dir}; run data/fetch_filings.py first")

    eval_set = json.loads(
        (Path(__file__).parent / "data" / "eval_questions.json").read_text()
    )["questions"]

    filings = load_filings(filings_dir)
    print(f"corpus: {len(filings)} filings")

    per_seed: dict[int, dict] = {}
    for seed in SEEDS:
        print(f"\n=== seed {seed} ===")
        t0 = time.time()
        idx = build_corpus_index(filings, seed=seed)
        run = run_pipeline(idx, eval_set, seed=seed)
        result = evaluate(run.questions, run.answers, run.contexts, run.ground_truths)
        elapsed = time.time() - t0
        per_seed[seed] = {
            "faithfulness": result.faithfulness,
            "answer_relevance": result.answer_relevance,
            "context_precision": result.context_precision,
            "context_recall": result.context_recall,
            "transforms_used": run.transforms_used,
            "elapsed_s": elapsed,
        }
        print(f"seed {seed}: faith={result.faithfulness:.3f} "
              f"ans_rel={result.answer_relevance:.3f} "
              f"ctx_prec={result.context_precision:.3f} "
              f"ctx_rec={result.context_recall:.3f} ({elapsed:.0f}s)")

    faiths = [per_seed[s]["faithfulness"] for s in SEEDS]
    cprecs = [per_seed[s]["context_precision"] for s in SEEDS]
    arels = [per_seed[s]["answer_relevance"] for s in SEEDS]
    crecs = [per_seed[s]["context_recall"] for s in SEEDS]

    summary = {
        "n_filings": len(filings),
        "n_questions": len(eval_set),
        "seeds": list(SEEDS),
        "per_seed": per_seed,
        "summary": {
            "faithfulness_mean": sum(faiths) / len(faiths),
            "faithfulness_stdev": _stdev(faiths),
            "answer_relevance_mean": sum(arels) / len(arels),
            "answer_relevance_stdev": _stdev(arels),
            "context_precision_mean": sum(cprecs) / len(cprecs),
            "context_precision_stdev": _stdev(cprecs),
            "context_recall_mean": sum(crecs) / len(crecs),
            "context_recall_stdev": _stdev(crecs),
        },
        "thresholds": {
            "faithfulness": FAITHFULNESS_THRESHOLD,
            "context_precision": CONTEXT_PRECISION_THRESHOLD,
        },
    }

    out_path = Path(__file__).parent / "data" / "proxy_run_results.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))

    s = summary["summary"]
    print(f"\n--- proxy run ({len(filings)} filings × {len(SEEDS)} seeds) ---")
    print(f"faithfulness      : {s['faithfulness_mean']:.3f} ± {s['faithfulness_stdev']:.3f}  "
          f"(threshold {FAITHFULNESS_THRESHOLD})")
    print(f"answer_relevance  : {s['answer_relevance_mean']:.3f} ± {s['answer_relevance_stdev']:.3f}")
    print(f"context_precision : {s['context_precision_mean']:.3f} ± {s['context_precision_stdev']:.3f}  "
          f"(threshold {CONTEXT_PRECISION_THRESHOLD})")
    print(f"context_recall    : {s['context_recall_mean']:.3f} ± {s['context_recall_stdev']:.3f}")
    print(f"\nresults written to {out_path}")

    passed = (
        s["faithfulness_mean"] >= FAITHFULNESS_THRESHOLD
        and s["context_precision_mean"] >= CONTEXT_PRECISION_THRESHOLD
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
