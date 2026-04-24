"""A planted bug + the fix, with structlog for context-preserving logs.

Bug: HN API returns `None` for deleted items. The naive code does `item['title']`
which explodes with TypeError. Fix: guard against None + missing keys.
"""
from __future__ import annotations
import asyncio
import sys
import argparse
import httpx

try:
    import structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    log = structlog.get_logger()
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger()

HN = "https://hacker-news.firebaseio.com/v0"


async def fetch_title_buggy(client: httpx.AsyncClient, id: int) -> str:
    """Buggy version: crashes when item is None (deleted)."""
    r = await client.get(f"{HN}/item/{id}.json", timeout=10)
    item = r.json()
    return item["title"]  # BUG: item can be None; 'title' may be missing


async def fetch_title(client: httpx.AsyncClient, id: int) -> str | None:
    """Fixed version."""
    r = await client.get(f"{HN}/item/{id}.json", timeout=10)
    item = r.json()
    if not item:
        log.info("skip_deleted", id=id)
        return None
    return item.get("title")


async def run_buggy(ids: list[int]) -> list[str]:
    async with httpx.AsyncClient() as c:
        return [await fetch_title_buggy(c, i) for i in ids]


async def run_fixed(ids: list[int]) -> list[str]:
    async with httpx.AsyncClient() as c:
        out = []
        for i in ids:
            try:
                structlog_bind = getattr(
                    __import__("structlog").contextvars, "bind_contextvars", lambda **_: None
                )
                structlog_bind(item_id=i)
            except Exception:
                pass
            t = await fetch_title(c, i)
            if t is not None:
                out.append(t)
        return out


# Mix of live IDs and a historically-deleted one (id=1 exists; id=2 deleted in the past).
SAMPLE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--find-bug", action="store_true")
    ap.add_argument("--fixed", action="store_true")
    args = ap.parse_args()
    if args.find_bug:
        try:
            titles = asyncio.run(run_buggy(SAMPLE_IDS))
            print("unexpected success:", titles)
            return 1
        except (TypeError, KeyError) as e:
            print(f"reproduced bug: {type(e).__name__}: {e}")
            return 0
    if args.fixed:
        titles = asyncio.run(run_fixed(SAMPLE_IDS))
        print(f"got {len(titles)} titles")
        return 0
    print("use --find-bug or --fixed")
    return 2


if __name__ == "__main__":
    sys.exit(main())
