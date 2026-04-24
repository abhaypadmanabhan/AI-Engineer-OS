"""Solution: HyDE, decomposition, step-back, multi-query — each a single Sonnet call
that rewrites the query into one or more strings, then reuses 3.6's hybrid(BM25+dense+RRF)
retriever and RRF-fuses across rewrites. Same 20-Q arXiv eval as 3.3–3.6.
"""
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from anthropic import Anthropic

# Reuse 3.6 primitives verbatim — do not re-invent.
sys.path.insert(0, str(Path(__file__).parent.parent / "06-hybrid-rerank"))
from solution import build_index, eval_config, load_corpus, rrf  # noqa: E402

import voyageai  # noqa: E402

EVAL_PATH = Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json"
MODEL = "claude-sonnet-4-6"
vo = voyageai.Client()
client = Anthropic()


def _complete(prompt: str, max_tokens: int = 400) -> str:
    r = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()


def hyde(q: str) -> list[str]:
    """Hypothetical Document Embeddings. Sonnet drafts an answer; we retrieve on THAT."""
    answer = _complete(
        f"Write a concise 2-3 sentence scientific-paper-style answer to: {q}\n"
        "Write as if excerpting from the paper itself. No preamble."
    )
    return [answer]


def decompose(q: str) -> list[str]:
    """Multi-hop → sub-queries. Each retrieved independently, then RRF-fused."""
    raw = _complete(
        f"Break this question into 2-3 atomic sub-questions, one per line. "
        f"Skip if already atomic (return the question unchanged).\nQ: {q}"
    )
    subs = [re.sub(r"^[\d.\-)\s]+", "", line).strip() for line in raw.splitlines() if line.strip()]
    return subs or [q]


def step_back(q: str) -> list[str]:
    """Generate one-level-up abstraction. Keep the original too."""
    abstract = _complete(
        f"Rewrite this question one level more abstract (e.g. 'attention in Transformers' "
        f"→ 'neural sequence model architectures'). One line, no preamble.\nQ: {q}"
    )
    return [q, abstract]


def multi_query(q: str, n: int = 3) -> list[str]:
    """Generate n paraphrases. Cheap, broad coverage."""
    raw = _complete(
        f"Paraphrase this question {n} different ways, one per line. No numbering.\nQ: {q}",
        max_tokens=300,
    )
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return [q] + lines[:n]


def make_transform_retriever(
    transform_fn, hybrid_topk, k_per_query: int = 30,
) -> callable:
    """Wrap a transform + the hybrid retriever: transform → hybrid retrieve each rewrite → RRF fuse."""
    def retrieve(q: str, k: int) -> list[int]:
        queries = transform_fn(q)
        rankings = [np.array(hybrid_topk(qi, k_per_query)) for qi in queries]
        return rrf(rankings, k)
    return retrieve


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("VOYAGE_API_KEY")
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

    configs = {
        "hybrid_baseline": hybrid_topk,
        "hyde": make_transform_retriever(hyde, hybrid_topk),
        "decompose": make_transform_retriever(decompose, hybrid_topk),
        "step_back": make_transform_retriever(step_back, hybrid_topk),
        "multi_query": make_transform_retriever(multi_query, hybrid_topk),
    }
    best = 0.0
    for name, fn in configs.items():
        score = eval_config(fn, corpus, eval_set, k=10)
        print(f"{name:<18} nDCG@10={score:.3f}")
        best = max(best, score)
    print(f"ndcg_at_10={best:.3f}")


if __name__ == "__main__":
    main()
