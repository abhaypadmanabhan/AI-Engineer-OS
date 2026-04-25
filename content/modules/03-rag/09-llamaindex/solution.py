"""LlamaIndex reveal: 3.3's 50-line naive RAG in 15 lines, plus the naive version
side-by-side for apples-to-apples nDCG@10 on the 20-Q arXiv eval set.

Exposes two retrievers with the same signature — `retrieve(q, k) -> list[str]`
returning arXiv IDs — so eval.py can score them identically.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

ARXIV_DIR = Path(__file__).parent.parent / "03-naive-rag" / "data" / "arxiv"


# ---------- The 15-line LlamaIndex version -------------------------------
def build_llamaindex_retriever(top_k: int = 10):
    from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
    from llama_index.embeddings.cohere import CohereEmbedding
    from llama_index.llms.anthropic import Anthropic

    Settings.llm = Anthropic(model="claude-sonnet-4-6")
    Settings.embed_model = CohereEmbedding(model_name="embed-english-v3.0")

    docs = SimpleDirectoryReader(str(ARXIV_DIR)).load_data()
    index = VectorStoreIndex.from_documents(docs)
    retriever = index.as_retriever(similarity_top_k=top_k)

    def retrieve(q: str, k: int) -> list[str]:
        nodes = retriever.retrieve(q)[:k]
        # SimpleDirectoryReader puts filename in node.metadata["file_name"] → "1706.03762.txt"
        return [Path(n.node.metadata.get("file_name", "")).stem for n in nodes]

    return retrieve


# ---------- The 50-line naive version, trimmed for parity -----------------
def build_naive_retriever(top_k: int = 10):
    import cohere

    co = cohere.Client(api_key=os.environ["COHERE_API_KEY"])
    texts: list[str] = []
    arxiv_ids: list[str] = []
    for path in sorted(ARXIV_DIR.glob("*.txt")):
        t = path.read_text()
        for i in range(0, len(t), 500):
            texts.append(t[i : i + 500])
            arxiv_ids.append(path.stem)
    E = np.array(co.embed(texts=texts, model="embed-english-v3.0", input_type="search_document").embeddings)
    E /= np.linalg.norm(E, axis=1, keepdims=True)

    def retrieve(q: str, k: int) -> list[str]:
        qe = np.array(co.embed(texts=[q], model="embed-english-v3.0", input_type="search_query").embeddings[0])
        qe /= np.linalg.norm(qe)
        order = np.argsort(-(E @ qe))[:k]
        return [arxiv_ids[i] for i in order]

    return retrieve


# ---------- nDCG (duplicated from 3.6 per repo convention) ----------------
def ndcg_at_k(retrieved_ids: list[str], expected_id: str, k: int = 10) -> float:
    import math

    rels = [1 if d == expected_id else 0 for d in retrieved_ids[:k]]
    def dcg(xs): return sum(r / math.log2(i + 2) for i, r in enumerate(xs))
    ideal = dcg(sorted(rels, reverse=True))
    return dcg(rels) / ideal if ideal else 0.0


def eval_retriever(retrieve, eval_set, k: int = 10) -> float:
    scores = [ndcg_at_k(retrieve(x["question"], k), x["expected_arxiv_id"], k)
              for x in eval_set]
    return sum(scores) / len(scores)


def main() -> None:
    assert os.environ.get("COHERE_API_KEY") and os.environ.get("ANTHROPIC_API_KEY")
    import json

    eval_set = json.loads(
        (Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json").read_text()
    )
    for name, builder in [
        ("naive_50_lines", build_naive_retriever),
        ("llamaindex_15_lines", build_llamaindex_retriever),
    ]:
        r = builder()
        score = eval_retriever(r, eval_set, k=10)
        print(f"{name:<22} nDCG@10={score:.3f}")


if __name__ == "__main__":
    main()
