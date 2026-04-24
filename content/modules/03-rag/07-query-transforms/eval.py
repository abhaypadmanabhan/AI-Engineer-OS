"""Eval: best query-transform nDCG@10 >= 0.85, must beat hybrid baseline (~0.80)."""
import os
import sys

THRESHOLD = 0.85


def main() -> int:
    if not (os.environ.get("VOYAGE_API_KEY") and os.environ.get("ANTHROPIC_API_KEY")):
        print("skip: VOYAGE_API_KEY and ANTHROPIC_API_KEY required")
        return 1
    import json
    from pathlib import Path

    import numpy as np
    import voyageai

    from solution import (
        decompose,
        eval_config,
        hyde,
        load_corpus,
        build_index,
        make_transform_retriever,
        multi_query,
        rrf,
        step_back,
    )

    vo = voyageai.Client()
    corpus = load_corpus()
    texts, E, bm25 = build_index(corpus)
    eval_set = json.loads(
        (Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json").read_text()
    )

    def dense_topk(q, k):
        qe = np.array(vo.embed([q], model="voyage-3", input_type="query").embeddings[0])
        qe /= np.linalg.norm(qe)
        return list(np.argsort(-(E @ qe))[:k])

    def bm25_topk(q, k):
        return list(np.argsort(-np.array(bm25.get_scores(q.lower().split())))[:k])

    def hybrid_topk(q, k):
        return rrf([np.array(dense_topk(q, 50)), np.array(bm25_topk(q, 50))], k)

    configs = {
        "hybrid_baseline": hybrid_topk,
        "hyde": make_transform_retriever(hyde, hybrid_topk),
        "decompose": make_transform_retriever(decompose, hybrid_topk),
        "step_back": make_transform_retriever(step_back, hybrid_topk),
        "multi_query": make_transform_retriever(multi_query, hybrid_topk),
    }
    best = 0.0
    best_name = ""
    for name, fn in configs.items():
        s = eval_config(fn, corpus, eval_set, k=10)
        print(f"{name:<18} nDCG@10={s:.3f}")
        if s > best:
            best, best_name = s, name

    print(f"best={best_name} ndcg_at_10={best:.3f} threshold={THRESHOLD}")
    return 0 if best >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
