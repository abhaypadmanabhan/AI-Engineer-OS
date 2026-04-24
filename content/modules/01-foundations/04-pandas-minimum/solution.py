"""Pandas minimum: pull real HN, save CSV, run the groupby, emit clean records."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

CSV = Path(__file__).parent / "hn_top.csv"
HN = "https://hacker-news.firebaseio.com/v0"


def write_sample(n: int = 50) -> Path:
    """Fetch N real HN top stories synchronously and cache as CSV."""
    import urllib.request

    def _get(url: str) -> dict | list:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())

    ids = _get(f"{HN}/topstories.json")[:n]
    rows = []
    for i in ids:
        item = _get(f"{HN}/item/{i}.json") or {}
        rows.append(
            {
                "id": item.get("id"),
                "by": item.get("by"),
                "score": item.get("score"),
                "descendants": item.get("descendants"),
                "title": item.get("title"),
                "url": item.get("url"),
                "time": item.get("time"),
            }
        )
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
    df.to_csv(CSV, index=False)
    return CSV


def load() -> pd.DataFrame:
    return pd.read_csv(
        CSV,
        dtype={"id": "Int64", "score": "Int64", "descendants": "Int64"},
        parse_dates=["time"],
    )


def by_author(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("by", dropna=True)
        .agg(
            stories=("id", "count"),
            total_score=("score", "sum"),
            mean_score=("score", "mean"),
        )
        .sort_values("total_score", ascending=False)
    )


def to_records(df: pd.DataFrame) -> list[dict]:
    return (
        df.assign(time=lambda d: d["time"].astype(str))
        .replace({np.nan: None})
        .to_dict(orient="records")
    )


if __name__ == "__main__":
    if not CSV.exists():
        write_sample()
    df = load()
    print(df.dtypes)
    print(by_author(df).head(5))
    recs = to_records(df.head(3))
    print(json.dumps(recs, indent=2, default=str))
