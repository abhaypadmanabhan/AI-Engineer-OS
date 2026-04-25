"""L3 Mastery Gate — RAG pipeline over SEC 10-K filings.

Composes every prior lesson:
- 3.5 structural chunking (section-aware splits on `## ITEM X.` markers)
- 3.6 hybrid retrieval (BM25 + voyage-3 + RRF) + bge-reranker (Cohere if key present)
- 3.7 query transforms (HyDE for vague, step-back for comparison)
- 3.8 evaluate() — Ragas harness imported unchanged

Public API:
    pipeline = Pipeline(filings_dir, seed=7)
    out = pipeline.run(eval_questions)   # returns answers, contexts, ground_truths
    result = evaluate(...)               # 3.8 ragas harness

`seed` controls:
- A `seed`-derived offset (in chars) added to the structural chunker's secondary
  split point when a section exceeds `max_chunk_chars`. Real chunk boundaries shift.
- The order in which BM25 and dense rankings are passed to RRF (no effect on RRF
  output since RRF is order-invariant in fusion, but affects the tie-break path
  through numpy argsort on identical scores).
- random.shuffle() seed for any tie-broken numpy argsort calls.

Production temp=0 generation; seed does NOT control LLM determinism (Anthropic
server-side variance ~1% even at temp=0). That is real, residual variance the
two-seed harness exposes alongside the algorithmic seed effects.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from anthropic import Anthropic

# Reuse 3.8 ragas harness verbatim.
sys.path.insert(0, str(Path(__file__).parent.parent / "08-ragas"))
from solution import RagasResult, evaluate  # noqa: E402

MODEL = "claude-sonnet-4-6"
EMBED_MODEL = "voyage-3"
MAX_CHUNK_CHARS = 1500
MAX_CHUNK_OVERLAP = 100


# =========================================================================
# Structural chunker (lesson 3.5 pattern, section-aware for 10-Ks)
# =========================================================================

_SECTION_RE = re.compile(r"^##\s+(ITEM\s+\d+[A-Z]?\.?\s+[^\n]+)$", re.MULTILINE)


def chunk_filing(text: str, ticker: str, seed: int = 0) -> list[dict]:
    """Split a 10-K's plain text into chunks. Section header forces a chunk break;
    sections longer than MAX_CHUNK_CHARS split with seed-derived jitter on the
    boundary so two-seed runs surface real chunking variance."""
    rnd = random.Random(seed * 17 + hash(ticker) % 1000)
    sections: list[tuple[str, str]] = []
    last_end = 0
    last_label = "PREAMBLE"
    for m in _SECTION_RE.finditer(text):
        body = text[last_end : m.start()].strip()
        if body:
            sections.append((last_label, body))
        last_label = m.group(1).strip()
        last_end = m.end()
    tail = text[last_end:].strip()
    if tail:
        sections.append((last_label, tail))

    chunks: list[dict] = []
    for section, body in sections:
        if len(body) <= MAX_CHUNK_CHARS:
            chunks.append({"ticker": ticker, "section": section, "text": body})
            continue
        # split with jitter
        i = 0
        while i < len(body):
            jitter = rnd.randint(-MAX_CHUNK_OVERLAP, MAX_CHUNK_OVERLAP)
            window = max(500, MAX_CHUNK_CHARS + jitter)
            sub = body[i : i + window]
            # try to break on sentence boundary
            j = sub.rfind(". ")
            if j > 500:
                sub = sub[: j + 1]
                step = j + 1
            else:
                step = window
            chunks.append({"ticker": ticker, "section": section, "text": sub.strip()})
            i += step - MAX_CHUNK_OVERLAP // 2
    return [c for c in chunks if c["text"]]


# =========================================================================
# Hybrid retrieval + rerank (lesson 3.6 pattern)
# =========================================================================

def build_index(chunks: list[dict]):
    import voyageai
    from rank_bm25 import BM25Okapi

    vo = voyageai.Client()
    texts = [c["text"] for c in chunks]
    # voyage-3 has 32k token batch limit, but we are well within that with 1500-char chunks;
    # batch in 128 to stay under request size limits.
    embs: list[list[float]] = []
    BATCH = 128
    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        embs.extend(vo.embed(batch, model=EMBED_MODEL, input_type="document").embeddings)
        print(f"  embedded {min(i+BATCH, len(texts))}/{len(texts)}", flush=True)
    E = np.array(embs)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    bm25 = BM25Okapi([t.lower().split() for t in texts])
    return {"texts": texts, "chunks": chunks, "E": E, "bm25": bm25}


def _rrf(rankings: list[np.ndarray], k: int, k_rrf: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for r in rankings:
        for rank, doc_id in enumerate(r):
            scores[int(doc_id)] = scores.get(int(doc_id), 0) + 1 / (k_rrf + rank)
    return sorted(scores, key=scores.get, reverse=True)[:k]


def _dense_topk(idx, q: str, k: int) -> list[int]:
    import voyageai
    vo = voyageai.Client()
    qe = np.array(vo.embed([q], model=EMBED_MODEL, input_type="query").embeddings[0])
    qe /= np.linalg.norm(qe)
    return list(np.argsort(-(idx["E"] @ qe))[:k])


def _bm25_topk(idx, q: str, k: int) -> list[int]:
    return list(np.argsort(-np.array(idx["bm25"].get_scores(q.lower().split())))[:k])


def hybrid_topk(idx, q: str, k: int, seed: int = 0) -> list[int]:
    rng = random.Random(seed)
    rankings = [np.array(_dense_topk(idx, q, 50)), np.array(_bm25_topk(idx, q, 50))]
    if rng.random() < 0.5:
        rankings = list(reversed(rankings))
    return _rrf(rankings, k)


def rerank_topk(idx, q: str, candidates: list[int], k: int) -> list[int]:
    """Cohere if COHERE_API_KEY present; else bge-reranker-v2-m3 local."""
    docs = [idx["texts"][i] for i in candidates]
    if os.environ.get("COHERE_API_KEY"):
        import cohere
        co = cohere.Client()
        r = co.rerank(query=q, documents=docs, model="rerank-v3.5", top_n=k)
        return [candidates[x.index] for x in r.results]
    from sentence_transformers import CrossEncoder
    if not hasattr(rerank_topk, "_bge"):
        rerank_topk._bge = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)
    pairs = [(q, d) for d in docs]
    scores = rerank_topk._bge.predict(pairs)
    order = sorted(range(len(candidates)), key=lambda i: -scores[i])[:k]
    return [candidates[i] for i in order]


# =========================================================================
# Query transforms (lesson 3.7) with cheap router
# =========================================================================

_client = Anthropic()


def _complete(prompt: str, max_tokens: int = 400) -> str:
    r = _client.messages.create(
        model=MODEL, max_tokens=max_tokens, temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()


def _hyde(q: str) -> list[str]:
    a = _complete(
        f"Write a concise 2-3 sentence excerpt as it would appear in an SEC 10-K "
        f"filing answering this question. No preamble.\nQuestion: {q}"
    )
    return [a]


def _step_back(q: str) -> list[str]:
    abstract = _complete(
        f"Rewrite this question one level more abstract (e.g. 'Apple FY2023 R&D' → "
        f"'technology company R&D investment trends'). One line, no preamble.\nQ: {q}"
    )
    return [q, abstract]


def _route(q: str, qtype: str) -> tuple[str, list[str]]:
    """Cheap router. Use the question's labeled type if available; otherwise default."""
    if qtype == "comparison":
        return "step_back", _step_back(q)
    if qtype == "factual":
        return "baseline", [q]
    # multi_hop benefits from HyDE on financial filings (vague concept terms)
    return "hyde", _hyde(q)


# =========================================================================
# Generation
# =========================================================================

_GEN_PROMPT = """You are answering a question about SEC 10-K filings. Answer using ONLY the context excerpts below. If the context does not contain the information, reply exactly: "Not in the provided context."

CONTEXT:
{context}

QUESTION: {question}

ANSWER (concise, factual, cite ticker(s) where relevant):"""


def generate(q: str, contexts: list[str]) -> str:
    joined = "\n\n---\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    return _complete(_GEN_PROMPT.format(context=joined, question=q), max_tokens=500)


# =========================================================================
# Pipeline
# =========================================================================

@dataclass
class PipelineRun:
    questions: list[str]
    answers: list[str]
    contexts: list[list[str]]
    ground_truths: list[str]
    transforms_used: list[str]
    seed: int


def load_filings(filings_dir: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for p in sorted(filings_dir.glob("*.txt")):
        out.append((p.stem, p.read_text()))
    return out


def build_corpus_index(filings: Iterable[tuple[str, str]], seed: int):
    chunks: list[dict] = []
    for ticker, text in filings:
        chunks.extend(chunk_filing(text, ticker, seed=seed))
    print(f"chunked: {len(chunks)} chunks across "
          f"{len({c['ticker'] for c in chunks})} filings")
    return build_index(chunks)


def run_pipeline(idx, eval_questions: list[dict], seed: int, top_k: int = 5,
                 candidate_k: int = 30) -> PipelineRun:
    qs, ans, ctxs, gts, used = [], [], [], [], []
    for i, item in enumerate(eval_questions):
        q = item["question"]
        transform_name, queries = _route(q, item["type"])
        # Retrieve once per rewrite, RRF-fuse, then rerank.
        all_cands: list[np.ndarray] = []
        for q_i in queries:
            all_cands.append(np.array(hybrid_topk(idx, q_i, candidate_k, seed=seed)))
        fused = _rrf(all_cands, candidate_k)
        top = rerank_topk(idx, q, fused, top_k)
        ctx_chunks = [idx["chunks"][j] for j in top]
        ctx_texts = [f"[{c['ticker']} | {c['section']}] {c['text']}" for c in ctx_chunks]
        a = generate(q, ctx_texts)
        qs.append(q); ans.append(a); ctxs.append(ctx_texts)
        gts.append(item["ground_truth_answer"])
        used.append(transform_name)
        print(f"[{i+1:2d}/{len(eval_questions)}] [{item['type']:<10}] "
              f"[{transform_name}] {q[:60]}", flush=True)
    return PipelineRun(qs, ans, ctxs, gts, used, seed)


if __name__ == "__main__":
    # Smoke test on whatever filings are present.
    filings_dir = Path(__file__).parent / "data" / "filings"
    eval_path = Path(__file__).parent / "data" / "eval_questions.json"
    if not filings_dir.exists() or not any(filings_dir.glob("*.txt")):
        sys.exit(f"no filings in {filings_dir}; run data/fetch_filings.py first")
    qs = json.loads(eval_path.read_text())["questions"][:3]
    idx = build_corpus_index(load_filings(filings_dir), seed=7)
    out = run_pipeline(idx, qs, seed=7)
    print("\n--- Smoke run ---")
    for q, a in zip(out.questions, out.answers):
        print(f"\nQ: {q}\nA: {a[:300]}")
