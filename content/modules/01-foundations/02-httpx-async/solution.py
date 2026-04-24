"""Parallel HN top-story fetcher with pooled httpx + tenacity retries."""
from __future__ import annotations
import asyncio
import time
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

HN = "https://hacker-news.firebaseio.com/v0"


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    wait=wait_exponential_jitter(initial=0.5, max=8),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def fetch(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url, timeout=httpx.Timeout(connect=3, read=10, write=5, pool=2))
    if r.status_code in (429, 503):
        raise httpx.HTTPStatusError("backoff", request=r.request, response=r)
    r.raise_for_status()
    return r.json()


async def top_stories(n: int = 100, concurrency: int = 20) -> list[dict]:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency // 2)
    async with httpx.AsyncClient(limits=limits) as client:
        ids = await fetch(client, f"{HN}/topstories.json")
        ids = ids[:n]
        sem = asyncio.Semaphore(concurrency)

        async def bounded(i: int) -> dict:
            async with sem:
                return await fetch(client, f"{HN}/item/{i}.json")

        return await asyncio.gather(*(bounded(i) for i in ids))


async def benchmark(n: int = 100) -> tuple[int, float, float]:
    t0 = time.perf_counter()
    stories = await top_stories(n)
    elapsed = time.perf_counter() - t0
    rps = len(stories) / elapsed if elapsed else 0.0
    return len(stories), elapsed, rps


if __name__ == "__main__":
    count, elapsed, rps = asyncio.run(benchmark(100))
    print(f"fetched={count} elapsed={elapsed:.2f}s rps={rps:.1f}")
