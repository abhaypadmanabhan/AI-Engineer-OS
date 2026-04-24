"""HN top-stories CLI: fetch -> validate -> emit JSON.

Usage:
    python solution.py top --limit 20 --json
    python solution.py top --limit 10
"""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from typing import Optional

import httpx
from pydantic import BaseModel, Field, ValidationError, HttpUrl
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

HN = "https://hacker-news.firebaseio.com/v0"


class Story(BaseModel):
    id: int
    by: str
    title: str = Field(min_length=1)
    score: int = Field(ge=0)
    time: int
    url: Optional[HttpUrl] = None
    descendants: Optional[int] = Field(default=None, ge=0)


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    wait=wait_exponential_jitter(initial=0.3, max=5),
    stop=stop_after_attempt(4),
    reraise=True,
)
async def _get(client: httpx.AsyncClient, url: str):
    r = await client.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


async def top_stories(limit: int) -> list[dict]:
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    async with httpx.AsyncClient(limits=limits) as c:
        # Over-fetch a bit so deleted/invalid items don't starve the caller.
        ids = (await _get(c, f"{HN}/topstories.json"))[: max(limit * 2, limit + 10)]
        sem = asyncio.Semaphore(20)

        async def one(i: int):
            async with sem:
                return await _get(c, f"{HN}/item/{i}.json")

        return await asyncio.gather(*(one(i) for i in ids))


def validate_rows(raw: list[dict], limit: int) -> list[Story]:
    out: list[Story] = []
    for item in raw:
        if not item:
            continue
        try:
            out.append(Story.model_validate(item))
        except ValidationError:
            continue
        if len(out) >= limit:
            break
    return out


def parse_args():
    p = argparse.ArgumentParser(description="HN CLI")
    p.add_argument("command", choices=["top"])
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    return p.parse_args()


async def amain() -> int:
    args = parse_args()
    raw = await top_stories(args.limit)
    valid = validate_rows(raw, args.limit)
    if args.json:
        print(json.dumps([s.model_dump(mode="json") for s in valid], indent=2))
    else:
        for s in valid:
            print(f"{s.score:>4}  {s.title}  ({s.by})")
    if len(valid) < args.limit:
        print(f"warn: only {len(valid)}/{args.limit} validated", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    sys.exit(main())
