"""Run the proxy eval for a SINGLE seed with cost instrumentation.
Used by the dual-seed proxy harness. Prints cost + metrics; writes seed_<n>.json.
Hard-stops on gate failure (does not retry, does not iterate).
"""
import json
import os
import sys
import time
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit("usage: run_one_seed.py <seed>")
SEED = int(sys.argv[1])

FAITHFULNESS_THRESHOLD = 0.85
CONTEXT_PRECISION_THRESHOLD = 0.75

# ----- Cost instrumentation -----
COHERE_EMBED_USD_PER_1M = 0.10
SONNET_INPUT_USD_PER_1M = 3.0
SONNET_OUTPUT_USD_PER_1M = 15.0

cost: dict[str, float] = {
    "cohere_embed_tokens": 0,
    "sonnet_input_tokens": 0,
    "sonnet_output_tokens": 0,
    "cohere_embed_usd": 0.0,
    "sonnet_usd": 0.0,
}


_tpm_window: list[tuple[float, int]] = []  # (timestamp, tokens) — last 60s


def _hook_cohere_embed(orig_embed):
    """Intercept co.embed: count tokens, track TPM, retry on transient SSL/network errors."""
    def wrapped(self, *args, **kwargs):
        texts = kwargs.get("texts") or (args[0] if args else [])
        est_tokens = sum(len(t) // 4 + 1 for t in texts)
        cost["cohere_embed_tokens"] += est_tokens
        cost["cohere_embed_usd"] = cost["cohere_embed_tokens"] * COHERE_EMBED_USD_PER_1M / 1_000_000
        now = time.time()
        _tpm_window.append((now, est_tokens))
        cutoff = now - 60
        while _tpm_window and _tpm_window[0][0] < cutoff:
            _tpm_window.pop(0)
        cost["cohere_peak_tpm"] = max(cost.get("cohere_peak_tpm", 0),
                                      sum(t for _, t in _tpm_window))
        # retry on transient SSL/network/connection errors (cohere SDK uses httpx with
        # concurrent.futures internally; rare SSL state corruption surfaces as ReadError).
        import httpx
        for attempt in range(4):
            try:
                return orig_embed(self, *args, **kwargs)
            except (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                cost["cohere_retries"] = cost.get("cohere_retries", 0) + 1
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                print(f"  [embed retry {attempt+1}/3 after {type(e).__name__}]", flush=True)
        # unreachable
    return wrapped


def _hook_anthropic(orig_create):
    """Intercept client.messages.create to count actual usage tokens from response."""
    def wrapped(self, *args, **kwargs):
        r = orig_create(self, *args, **kwargs)
        u = getattr(r, "usage", None)
        if u:
            cost["sonnet_input_tokens"] += getattr(u, "input_tokens", 0) or 0
            cost["sonnet_output_tokens"] += getattr(u, "output_tokens", 0) or 0
            cost["sonnet_usd"] = (
                cost["sonnet_input_tokens"] * SONNET_INPUT_USD_PER_1M / 1_000_000
                + cost["sonnet_output_tokens"] * SONNET_OUTPUT_USD_PER_1M / 1_000_000
            )
        return r
    return wrapped


def _patch_clients() -> None:
    import cohere
    cohere.Client.embed = _hook_cohere_embed(cohere.Client.embed)
    from anthropic.resources.messages import Messages
    Messages.create = _hook_anthropic(Messages.create)


def main() -> int:
    missing = [k for k in ("ANTHROPIC_API_KEY", "COHERE_API_KEY") if not os.environ.get(k)]
    if missing:
        sys.exit(f"missing: {missing}")

    _patch_clients()

    sys.path.insert(0, str(Path(__file__).parent))
    from solution import build_corpus_index, evaluate, load_filings, run_pipeline

    filings_dir = Path(__file__).parent / "data" / "filings"
    eval_set = json.loads((Path(__file__).parent / "data" / "eval_questions.json").read_text())["questions"]
    filings = load_filings(filings_dir)
    print(f"[seed {SEED}] corpus: {len(filings)} filings, {len(eval_set)} questions")

    t0 = time.time()
    print(f"[seed {SEED}] building index…", flush=True)
    idx = build_corpus_index(filings, seed=SEED)
    t_index = time.time() - t0
    print(f"[seed {SEED}] index built in {t_index:.0f}s. cohere embed cost so far: ${cost['cohere_embed_usd']:.2f}", flush=True)

    # Pipeline checkpoint: re-use prior pipeline output if file present (skip 8-min retrieval+gen).
    pipe_path = Path(__file__).parent / "data" / f"seed_{SEED}_pipeline.json"
    if pipe_path.exists():
        print(f"[seed {SEED}] reusing pipeline checkpoint at {pipe_path}", flush=True)
        from solution import PipelineRun
        d = json.loads(pipe_path.read_text())
        run = PipelineRun(**d)
        t_pipe = 0.0
    else:
        t1 = time.time()
        print(f"[seed {SEED}] running pipeline (50 questions)…", flush=True)
        run = run_pipeline(idx, eval_set, seed=SEED)
        t_pipe = time.time() - t1
        # Save before ragas so a ragas crash doesn't waste pipeline work.
        pipe_path.write_text(json.dumps({
            "questions": run.questions, "answers": run.answers,
            "contexts": run.contexts, "ground_truths": run.ground_truths,
            "transforms_used": run.transforms_used, "seed": SEED,
        }, indent=2))
        print(f"[seed {SEED}] pipeline {t_pipe:.0f}s. checkpoint saved. running ragas…", flush=True)

    t2 = time.time()
    result = evaluate(run.questions, run.answers, run.contexts, run.ground_truths)
    t_ragas = time.time() - t2
    elapsed = time.time() - t0

    out = {
        "seed": SEED,
        "n_filings": len(filings),
        "n_questions": len(eval_set),
        "elapsed_s": elapsed,
        "elapsed_breakdown_s": {"index": t_index, "pipeline": t_pipe, "ragas": t_ragas},
        "metrics": {
            "faithfulness": result.faithfulness,
            "answer_relevance": result.answer_relevance,
            "context_precision": result.context_precision,
            "context_recall": result.context_recall,
        },
        "cost": cost,
        "transforms_used": run.transforms_used,
        "per_question": [
            {"id": q["id"], "type": q["type"], "transform": run.transforms_used[i],
             "answer": run.answers[i][:300], "first_ctx_tickers": [
                 c.split("|")[0].strip("[ ") for c in run.contexts[i][:3]
             ]}
            for i, q in enumerate(eval_set)
        ],
    }
    out_path = Path(__file__).parent / "data" / f"seed_{SEED}.json"
    out_path.write_text(json.dumps(out, indent=2))

    print(f"\n=== SEED {SEED} RESULT ({elapsed:.0f}s total) ===")
    print(f"  faithfulness     : {result.faithfulness:.3f}  (threshold {FAITHFULNESS_THRESHOLD})")
    print(f"  context_precision: {result.context_precision:.3f}  (threshold {CONTEXT_PRECISION_THRESHOLD})")
    print(f"  answer_relevance : {result.answer_relevance:.3f}  (informational)")
    print(f"  context_recall   : {result.context_recall:.3f}  (informational)")
    print(f"  cost: cohere=${cost['cohere_embed_usd']:.2f} sonnet=${cost['sonnet_usd']:.2f} "
          f"total=${cost['cohere_embed_usd'] + cost['sonnet_usd']:.2f}")
    print(f"  saved to {out_path}")

    passed = (
        result.faithfulness >= FAITHFULNESS_THRESHOLD
        and result.context_precision >= CONTEXT_PRECISION_THRESHOLD
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
