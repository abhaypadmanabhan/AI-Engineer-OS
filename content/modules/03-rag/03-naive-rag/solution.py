"""Naive RAG reference: 50-line pipeline + recall@5 on a 20-Q eval set."""
import json
import os
from pathlib import Path

import numpy as np
import cohere
from anthropic import Anthropic

co = cohere.Client(api_key=os.environ["COHERE_API_KEY"])
claude = Anthropic()
DATA = Path(__file__).parent / "data"


def chunk(text: str, size: int = 500) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def build_index() -> tuple[np.ndarray, list[tuple[str, str]]]:
    """Return (embeddings, [(chunk_text, arxiv_id)])."""
    corpus: list[tuple[str, str]] = []
    for path in sorted((DATA / "arxiv").glob("*.txt")):
        for c in chunk(path.read_text()):
            corpus.append((c, path.stem))
    texts = [c for c, _ in corpus]
    embs = np.array(co.embed(texts=texts, model="embed-english-v3.0", input_type="search_document").embeddings)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    return embs, corpus


def retrieve(query: str, embs: np.ndarray, corpus: list[tuple[str, str]], k: int = 5) -> list[tuple[str, str]]:
    qe = np.array(co.embed(texts=[query], model="embed-english-v3.0", input_type="search_query").embeddings[0])
    qe /= np.linalg.norm(qe)
    scores = embs @ qe
    return [corpus[i] for i in scores.argsort()[-k:][::-1]]


def ask(query: str, embs: np.ndarray, corpus: list[tuple[str, str]]) -> str:
    hits = retrieve(query, embs, corpus)
    ctx = "\n\n---\n\n".join(c for c, _ in hits)
    r = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        temperature=0,
        messages=[{"role": "user", "content": f"Context:\n{ctx}\n\nAnswer from context only: {query}"}],
    )
    return r.content[0].text


def recall_at_k(embs: np.ndarray, corpus: list[tuple[str, str]], k: int = 5) -> float:
    eval_set = json.loads((DATA / "eval_questions.json").read_text())
    hits = 0
    for item in eval_set:
        retrieved = retrieve(item["question"], embs, corpus, k=k)
        retrieved_ids = {aid for _, aid in retrieved}
        if item["expected_arxiv_id"] in retrieved_ids:
            hits += 1
    return hits / len(eval_set)


def main() -> None:
    assert os.environ.get("COHERE_API_KEY") and os.environ.get("ANTHROPIC_API_KEY")
    embs, corpus = build_index()
    score = recall_at_k(embs, corpus, k=5)
    print(f"recall_at_5={score:.2f}  (corpus={len(corpus)} chunks, docs={len({d for _, d in corpus})})")


if __name__ == "__main__":
    main()
