"""Eval: best nDCG@10 >= 0.80 across dense / hybrid / hybrid+rerank."""
import os
import sys


THRESHOLD = 0.80


def main() -> int:
    if not os.environ.get("VOYAGE_API_KEY"):
        print("skip: VOYAGE_API_KEY not set")
        return 1
    from solution import (
        build_index,
        eval_config,
        load_corpus,
        rrf,
    )
    import json
    from pathlib import Path
    import numpy as np
    import voyageai
    from rank_bm25 import BM25Okapi

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

    best = 0.0
    for name, fn in [("dense", dense_topk), ("hybrid", hybrid_topk)]:
        s = eval_config(fn, corpus, eval_set, k=10)
        print(f"{name}: nDCG@10={s:.3f}")
        best = max(best, s)

    if os.environ.get("COHERE_API_KEY"):
        import cohere
        co = cohere.Client()

        def hybrid_rerank(q, k):
            cands = hybrid_topk(q, 50)
            docs = [texts[i] for i in cands]
            r = co.rerank(query=q, documents=docs, model="rerank-v3.5", top_n=k)
            return [cands[x.index] for x in r.results]

        label = "hybrid_rerank_cohere"
    else:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            print("install sentence-transformers to run the free bge reranker fallback")
            print(f"ndcg_at_10={best:.3f} threshold={THRESHOLD}")
            return 0 if best >= THRESHOLD else 1
        bge = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)

        def hybrid_rerank(q, k):
            cands = hybrid_topk(q, 50)
            pairs = [(q, texts[i]) for i in cands]
            scores = bge.predict(pairs)
            order = sorted(range(len(cands)), key=lambda i: -scores[i])[:k]
            return [cands[i] for i in order]

        label = "hybrid_rerank_bge"

    s = eval_config(hybrid_rerank, corpus, eval_set, k=10)
    print(f"{label}: nDCG@10={s:.3f}")
    best = max(best, s)

    print(f"ndcg_at_10={best:.3f} threshold={THRESHOLD}")
    return 0 if best >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
