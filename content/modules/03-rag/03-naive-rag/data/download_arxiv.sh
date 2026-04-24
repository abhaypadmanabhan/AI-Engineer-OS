#!/usr/bin/env bash
# Fetch 100 arXiv abstracts across cs.CL / cs.CV / cs.LG. Idempotent.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p arxiv
python3 - <<'PY'
import pathlib, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET

OUT = pathlib.Path("arxiv")
OUT.mkdir(exist_ok=True)
NS = {"a": "http://www.w3.org/2005/Atom"}

queries = [
    ("cat:cs.CL", 40),
    ("cat:cs.CV", 30),
    ("cat:cs.LG", 30),
]
for q, n in queries:
    url = f"https://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending"
    data = urllib.request.urlopen(url).read()
    root = ET.fromstring(data)
    for entry in root.findall("a:entry", NS):
        aid = entry.find("a:id", NS).text.rsplit("/", 1)[-1].split("v")[0]
        title = (entry.find("a:title", NS).text or "").strip()
        summary = (entry.find("a:summary", NS).text or "").strip()
        (OUT / f"{aid}.txt").write_text(f"{title}\n\n{summary}")
    time.sleep(3)   # be kind to the arXiv API
print(f"fetched {len(list(OUT.glob('*.txt')))} abstracts into {OUT}/")
PY
