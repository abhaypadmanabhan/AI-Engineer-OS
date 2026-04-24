"""Eval: both pipelines on the 20-Q arXiv set. Gate: naive parity (nDCG@10 >= 0.65)
on the LlamaIndex version. This is a reveal lesson, not a win-vs-baseline lesson.
"""
import json
import os
import sys
from pathlib import Path

THRESHOLD = 0.65  # naive-parity; not a ceiling.


def main() -> int:
    if not (os.environ.get("VOYAGE_API_KEY") and os.environ.get("ANTHROPIC_API_KEY")):
        print("skip: VOYAGE_API_KEY and ANTHROPIC_API_KEY required")
        return 1

    sys.path.insert(0, str(Path(__file__).parent))
    from solution import (
        build_llamaindex_retriever,
        build_naive_retriever,
        eval_retriever,
    )

    eval_set = json.loads(
        (Path(__file__).parent.parent / "03-naive-rag" / "data" / "eval_questions.json").read_text()
    )

    naive = build_naive_retriever()
    li = build_llamaindex_retriever()

    s_naive = eval_retriever(naive, eval_set, k=10)
    s_li = eval_retriever(li, eval_set, k=10)
    print(f"naive_50_lines       nDCG@10={s_naive:.3f}")
    print(f"llamaindex_15_lines  nDCG@10={s_li:.3f}")
    print(f"ndcg_at_10={s_li:.3f} threshold={THRESHOLD}")
    return 0 if s_li >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
