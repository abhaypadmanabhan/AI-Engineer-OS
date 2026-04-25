"""Eval: recall@5 >= 0.6 on the 20-Q eval set over cached arXiv abstracts."""
import json
import os
import sys
from pathlib import Path

THRESHOLD = 0.6
DATA = Path(__file__).parent / "data"


def main() -> int:
    if not os.environ.get("COHERE_API_KEY"):
        print("skip: COHERE_API_KEY not set")
        return 1
    if not (DATA / "arxiv").exists():
        print("skip: run data/download_arxiv.sh first")
        return 1

    import numpy as np
    import cohere

    co = cohere.Client(api_key=os.environ["COHERE_API_KEY"])

    def chunk(t: str, size: int = 500) -> list[str]:
        return [t[i : i + size] for i in range(0, len(t), size)]

    corpus: list[tuple[str, str]] = []
    for path in sorted((DATA / "arxiv").glob("*.txt")):
        for c in chunk(path.read_text()):
            corpus.append((c, path.stem))
    texts = [c for c, _ in corpus]
    embs = np.array(co.embed(texts=texts, model="embed-english-v3.0", input_type="search_document").embeddings)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)

    eval_set = json.loads((DATA / "eval_questions.json").read_text())
    hits = 0
    for item in eval_set:
        qe = np.array(co.embed(texts=[item["question"]], model="embed-english-v3.0", input_type="search_query").embeddings[0])
        qe /= np.linalg.norm(qe)
        top5 = embs @ qe
        retrieved_ids = {corpus[i][1] for i in top5.argsort()[-5:][::-1]}
        if item["expected_arxiv_id"] in retrieved_ids:
            hits += 1
    score = hits / len(eval_set)
    print(f"recall_at_5={score:.2f} threshold={THRESHOLD}")
    return 0 if score >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
