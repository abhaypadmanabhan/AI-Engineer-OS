"""Solution: benchmark 4 chunkers on the 3.3 eval set, report best recall@5."""
import json
import re
from pathlib import Path
from typing import Callable

import numpy as np
import voyageai

vo = voyageai.Client()
ARXIV_DIR = Path(__file__).parent.parent / "03-naive-rag" / "data" / "arxiv"
EVAL_PATH = Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json"


def fixed(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def recursive(text: str, size: int = 500) -> list[str]:
    if len(text) <= size:
        return [text]
    for sep in ["\n\n", "\n", ". ", " ", ""]:
        if sep in text:
            parts, buf = [], ""
            for piece in text.split(sep):
                add = piece + (sep if sep else "")
                if len(buf) + len(add) > size and buf:
                    parts.append(buf)
                    buf = add
                else:
                    buf += add
            if buf:
                parts.append(buf)
            out: list[str] = []
            for p in parts:
                out.extend(recursive(p, size) if len(p) > size else [p])
            return out
    return [text[i : i + size] for i in range(0, len(text), size)]


def semantic(text: str, size: int = 500, threshold_pct: int = 90) -> list[str]:
    sents = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    if len(sents) < 3:
        return [text]
    E = np.array(vo.embed(sents, model="voyage-3", input_type="document").embeddings)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    sims = (E[:-1] * E[1:]).sum(axis=1)
    cut = np.percentile(sims, 100 - threshold_pct)
    chunks, buf = [], sents[0]
    for i, s in enumerate(sents[1:]):
        if sims[i] < cut and len(buf) > 50:
            chunks.append(buf)
            buf = s
        else:
            buf = f"{buf}. {s}"
    chunks.append(buf)
    return chunks


def structural_md(text: str, size: int = 1200) -> list[str]:
    parts = re.split(r"(?=^#{1,3} )", text, flags=re.M)
    if len(parts) == 1:
        # arxiv abstracts have no markdown headings — fall back to paragraph split
        parts = [p for p in re.split(r"\n\n+", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        out.extend([p] if len(p) <= size else recursive(p, size))
    return [o.strip() for o in out if o.strip()]


def build_index(chunker: Callable[[str], list[str]]) -> tuple[np.ndarray, list[tuple[str, str]]]:
    corpus: list[tuple[str, str]] = []
    for path in sorted(ARXIV_DIR.glob("*.txt")):
        for c in chunker(path.read_text()):
            corpus.append((c, path.stem))
    texts = [c for c, _ in corpus]
    embs = np.array(vo.embed(texts, model="voyage-3", input_type="document").embeddings)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    return embs, corpus


def recall_at_k(embs: np.ndarray, corpus: list[tuple[str, str]], k: int = 5) -> float:
    eval_set = json.loads(EVAL_PATH.read_text())
    hits = 0
    for item in eval_set:
        qe = np.array(vo.embed([item["question"]], model="voyage-3", input_type="query").embeddings[0])
        qe /= np.linalg.norm(qe)
        top = (embs @ qe).argsort()[-k:][::-1]
        if item["expected_arxiv_id"] in {corpus[i][1] for i in top}:
            hits += 1
    return hits / len(eval_set)


def main() -> None:
    best = 0.0
    for name, fn in [("fixed", fixed), ("recursive", recursive), ("semantic", semantic), ("structural_md", structural_md)]:
        embs, corpus = build_index(fn)
        r = recall_at_k(embs, corpus, k=5)
        print(f"{name:<14} recall@5={r:.2f}  chunks={len(corpus)}")
        best = max(best, r)
    print(f"best_chunker_recall_at_5={best:.2f}")


if __name__ == "__main__":
    main()
