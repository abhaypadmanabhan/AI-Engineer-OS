"""Eval: best chunker recall@5 >= 0.75 on the 3.3 eval set."""
import os
import sys
from pathlib import Path

THRESHOLD = 0.75


def main() -> int:
    if not os.environ.get("VOYAGE_API_KEY"):
        print("skip: VOYAGE_API_KEY not set")
        return 1
    arxiv_dir = Path(__file__).parent.parent / "03-naive-rag" / "data" / "arxiv"
    if not arxiv_dir.exists():
        print("skip: run 03-naive-rag/data/download_arxiv.sh first")
        return 1

    from solution import build_index, recall_at_k, fixed, recursive, semantic, structural_md

    best = 0.0
    for name, fn in [("fixed", fixed), ("recursive", recursive), ("semantic", semantic), ("structural_md", structural_md)]:
        embs, corpus = build_index(fn)
        r = recall_at_k(embs, corpus, k=5)
        print(f"{name}: recall@5={r:.2f} chunks={len(corpus)}")
        best = max(best, r)
    print(f"best_chunker_recall_at_5={best:.2f} threshold={THRESHOLD}")
    return 0 if best >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
