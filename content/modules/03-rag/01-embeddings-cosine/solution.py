"""Solution: hand-rolled cosine matches sklearn on 10 random vector pairs."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def main() -> None:
    rng = np.random.default_rng(0)
    pairs = [(rng.standard_normal(1024), rng.standard_normal(1024)) for _ in range(10)]
    ok = 0
    for a, b in pairs:
        mine = cosine(a, b)
        ref = float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0, 0])
        if abs(mine - ref) < 1e-6:
            ok += 1
    score = ok / len(pairs)
    print(f"cosine_correctness={score:.1f}")


if __name__ == "__main__":
    main()
