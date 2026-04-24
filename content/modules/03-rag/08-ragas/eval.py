"""Eval: run the 3.7 hybrid+HyDE pipeline on the 20-Q arXiv set, generate answers
with Sonnet, score with the Ragas harness. Gate: faithfulness >= 0.80."""
import json
import os
import sys
from pathlib import Path

FAITHFULNESS_THRESHOLD = 0.85
CONTEXT_PRECISION_THRESHOLD = 0.75


def main() -> int:
    missing = [k for k in ("ANTHROPIC_API_KEY", "VOYAGE_API_KEY") if not os.environ.get(k)]
    if missing:
        print(f"skip: missing {', '.join(missing)}")
        return 1

    # Reuse 3.7 retrieval stack.
    import numpy as np
    from anthropic import Anthropic

    sys.path.insert(0, str(Path(__file__).parent.parent / "06-hybrid-rerank"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "07-query-transforms"))
    from solution import build_index, load_corpus, rrf  # noqa: E402  (3.6)
    from solution import hyde, make_transform_retriever  # noqa: E402  (3.7)
    import voyageai

    # Ragas harness.
    sys.path.insert(0, str(Path(__file__).parent))
    from solution import evaluate  # noqa: E402

    vo = voyageai.Client()
    client = Anthropic()

    corpus = load_corpus()
    texts, E, bm25 = build_index(corpus)

    eval_set = json.loads(
        (Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json").read_text()
    )
    gt_by_id = {g["arxiv_id"]: g["answer"]
                for g in json.loads((Path(__file__).parent / "data" / "ground_truth_answers.json").read_text())}

    def dense_topk(q, k):
        qe = np.array(vo.embed([q], model="voyage-3", input_type="query").embeddings[0])
        qe /= np.linalg.norm(qe)
        return list(np.argsort(-(E @ qe))[:k])

    def bm25_topk(q, k):
        return list(np.argsort(-np.array(bm25.get_scores(q.lower().split())))[:k])

    def hybrid_topk(q, k):
        return rrf([np.array(dense_topk(q, 50)), np.array(bm25_topk(q, 50))], k)

    retriever = make_transform_retriever(hyde, hybrid_topk)

    def generate(q: str, ctx: list[str]) -> str:
        joined = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(ctx))
        prompt = (f"Answer the question using ONLY the context below. "
                  f"Be concise and factual.\n\nCONTEXT:\n{joined}\n\nQUESTION: {q}")
        r = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=400, temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text.strip()

    questions, answers, contexts, ground_truths = [], [], [], []
    for item in eval_set:
        q = item["question"]
        top_idx = retriever(q, 5)
        ctx = [texts[i] for i in top_idx]
        a = generate(q, ctx)
        questions.append(q)
        answers.append(a)
        contexts.append(ctx)
        ground_truths.append(gt_by_id[item["expected_arxiv_id"]])

    result = evaluate(questions, answers, contexts, ground_truths)
    print(json.dumps(result.as_dict(), indent=2))
    passed = (
        result.faithfulness >= FAITHFULNESS_THRESHOLD
        and result.context_precision >= CONTEXT_PRECISION_THRESHOLD
    )
    print(
        f"faithfulness={result.faithfulness:.3f} (>= {FAITHFULNESS_THRESHOLD}) "
        f"context_precision={result.context_precision:.3f} (>= {CONTEXT_PRECISION_THRESHOLD})"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
