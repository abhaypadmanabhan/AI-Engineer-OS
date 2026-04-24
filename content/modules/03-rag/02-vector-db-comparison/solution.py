"""Solution: Qdrant p95 query latency over 100 queries on 1k vectors."""
import time
import numpy as np
import statistics

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def main() -> None:
    client = QdrantClient(url="http://localhost:6333")
    client.recreate_collection(
        collection_name="arxiv_bench",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

    rng = np.random.default_rng(0)
    vecs = rng.standard_normal((1000, 1024)).astype("float32")
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    client.upsert(
        collection_name="arxiv_bench",
        points=[PointStruct(id=i, vector=vecs[i].tolist()) for i in range(1000)],
        wait=True,
    )

    queries = rng.standard_normal((100, 1024)).astype("float32")
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)

    lat_ms = []
    for q in queries:
        t0 = time.perf_counter()
        client.search(collection_name="arxiv_bench", query_vector=q.tolist(), limit=5)
        lat_ms.append((time.perf_counter() - t0) * 1000)

    p95 = statistics.quantiles(lat_ms, n=20)[18]
    print(f"qdrant_query_latency_p95_ms={p95:.1f}")


if __name__ == "__main__":
    main()
