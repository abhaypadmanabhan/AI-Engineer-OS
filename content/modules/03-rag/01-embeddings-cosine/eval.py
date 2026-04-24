"""Eval: pass if cosine_correctness == 1.0 on 10 random vector pairs."""
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

THRESHOLD = 1.0


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def main() -> int:
    rng = np.random.default_rng(0)
    pairs = [(rng.standard_normal(1024), rng.standard_normal(1024)) for _ in range(10)]
    ok = sum(
        abs(cosine(a, b) - float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0, 0])) < 1e-6
        for a, b in pairs
    )
    score = ok / len(pairs)
    print(f"cosine_correctness={score:.1f} threshold={THRESHOLD}")
    return 0 if score >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
