"""Solution: dense-only vs hybrid (BM25+dense+RRF) vs hybrid+Cohere-rerank, nDCG@10."""
import json
import math
import os
from pathlib import Path

import numpy as np
import voyageai
from rank_bm25 import BM25Okapi

vo = voyageai.Client()
ARXIV_DIR = Path(__file__).parent.parent / "03-naive-rag" / "data" / "arxiv"
EVAL_PATH = Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json"


def chunk(text: str, size: int = 500) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def load_corpus() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in sorted(ARXIV_DIR.glob("*.txt")):
        for c in chunk(path.read_text()):
            out.append((c, path.stem))
    return out


def build_index(corpus: list[tuple[str, str]]):
    texts = [c for c, _ in corpus]
    E = np.array(vo.embed(texts, model="voyage-3", input_type="document").embeddings)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    bm25 = BM25Okapi([t.lower().split() for t in texts])
    return texts, E, bm25


def rrf(rankings: list[np.ndarray], k: int, k_rrf: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for r in rankings:
        for rank, doc_id in enumerate(r):
            scores[int(doc_id)] = scores.get(int(doc_id), 0) + 1 / (k_rrf + rank)
    return sorted(scores, key=scores.get, reverse=True)[:k]


def dcg(rels: list[int]) -> float:
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(retrieved_doc_ids: list[str], expected_id: str, k: int = 10) -> float:
    rels = [1 if d == expected_id else 0 for d in retrieved_doc_ids[:k]]
    ideal = dcg(sorted(rels, reverse=True))
    return dcg(rels) / ideal if ideal else 0.0


def eval_config(get_retrieval, corpus, eval_set, k: int = 10) -> float:
    scores = []
    for item in eval_set:
        doc_ids = [corpus[i][1] for i in get_retrieval(item["question"], k)]
        scores.append(ndcg_at_k(doc_ids, item["expected_arxiv_id"], k))
    return sum(scores) / len(scores)


def main() -> None:
    assert os.environ.get("VOYAGE_API_KEY")
    corpus = load_corpus()
    texts, E, bm25 = build_index(corpus)
    eval_set = json.loads(EVAL_PATH.read_text())

    def dense_topk(q: str, k: int) -> list[int]:
        qe = np.array(vo.embed([q], model="voyage-3", input_type="query").embeddings[0])
        qe /= np.linalg.norm(qe)
        return list(np.argsort(-(E @ qe))[:k])

    def bm25_topk(q: str, k: int) -> list[int]:
        return list(np.argsort(-np.array(bm25.get_scores(q.lower().split())))[:k])

    def hybrid_topk(q: str, k: int) -> list[int]:
        return rrf([np.array(dense_topk(q, 50)), np.array(bm25_topk(q, 50))], k)

    def hybrid_rerank_topk(q: str, k: int) -> list[int]:
        cands = hybrid_topk(q, 50)
        if not os.environ.get("COHERE_API_KEY"):
            return cands[:k]
        import cohere
        co = cohere.Client()
        docs = [texts[i] for i in cands]
        r = co.rerank(query=q, documents=docs, model="rerank-v3.5", top_n=k)
        return [cands[x.index] for x in r.results]

    configs = {
        "dense_only": dense_topk,
        "hybrid_rrf": hybrid_topk,
        "hybrid_rerank": hybrid_rerank_topk,
    }
    best = 0.0
    for name, fn in configs.items():
        score = eval_config(fn, corpus, eval_set, k=10)
        print(f"{name:<15} nDCG@10={score:.3f}")
        best = max(best, score)
    print(f"ndcg_at_10={best:.3f}")


if __name__ == "__main__":
    main()
