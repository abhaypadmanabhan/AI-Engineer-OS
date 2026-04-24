"""Eval: Qdrant p95 query latency <= 50ms on 1k vectors."""
import sys
import time
import statistics
import numpy as np

THRESHOLD_MS = 50


def main() -> int:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
    except ImportError:
        print("skip: qdrant-client not installed")
        return 1

    try:
        client = QdrantClient(url="http://localhost:6333", timeout=2.0)
        client.get_collections()
    except Exception as e:
        print(f"skip: qdrant not reachable at :6333 ({e})")
        return 1

    client.recreate_collection(
        collection_name="eval_vdb",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    rng = np.random.default_rng(0)
    vecs = rng.standard_normal((1000, 1024)).astype("float32")
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    client.upsert(
        collection_name="eval_vdb",
        points=[PointStruct(id=i, vector=vecs[i].tolist()) for i in range(1000)],
        wait=True,
    )
    queries = rng.standard_normal((100, 1024)).astype("float32")
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)

    lat = []
    for q in queries:
        t0 = time.perf_counter()
        client.search(collection_name="eval_vdb", query_vector=q.tolist(), limit=5)
        lat.append((time.perf_counter() - t0) * 1000)

    p95 = statistics.quantiles(lat, n=20)[18]
    print(f"qdrant_query_latency_p95_ms={p95:.1f} threshold={THRESHOLD_MS}")
    return 0 if p95 <= THRESHOLD_MS else 1


if __name__ == "__main__":
    sys.exit(main())
