"""Ragas harness — faithfulness, answer_relevance, context_precision, context_recall.

Production signature. Reused verbatim by L3 mastery gate (3.10) and Capstone M2.
Raw Anthropic SDK; no teaching wrappers. The `ragas` pip package is an optional
cross-check in the lab — this module does not import it.

Public API:
    result = evaluate(questions, answers, contexts, ground_truths, judge_model=...)
    # RagasResult(faithfulness, answer_relevance, context_precision, context_recall)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
from anthropic import Anthropic

_client = Anthropic()


@dataclass
class RagasResult:
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float

    def as_dict(self) -> dict:
        return asdict(self)


# ---------- judge plumbing -------------------------------------------------

def _judge(prompt: str, model: str, max_tokens: int = 800) -> str:
    r = _client.messages.create(
        model=model, max_tokens=max_tokens, temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()


def _parse_json(text: str) -> Optional[dict | list]:
    """Tolerant JSON extraction — judges sometimes wrap in prose or code fences."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


# ---------- metric 1: faithfulness ----------------------------------------
# Claim extraction from answer, per-claim entailment against retrieved context.

_CLAIM_PROMPT = """Extract atomic factual claims from the answer. One claim per line, no numbering.
Skip opinions, questions, and meta-commentary. Only verifiable factual statements.

Answer: {answer}

Claims:"""

_ENTAIL_PROMPT = """Is the CLAIM supported by the CONTEXT? Reply with exactly one word: yes or no.

CONTEXT:
{context}

CLAIM: {claim}

Answer:"""


def _extract_claims(answer: str, model: str) -> list[str]:
    raw = _judge(_CLAIM_PROMPT.format(answer=answer), model, max_tokens=500)
    return [re.sub(r"^[\d.\-)\s]+", "", line).strip()
            for line in raw.splitlines() if line.strip()]


def _faithfulness_one(answer: str, context: list[str], model: str) -> float:
    claims = _extract_claims(answer, model)
    if not claims:
        return 1.0
    ctx = "\n\n".join(context)
    supported = 0
    for claim in claims:
        reply = _judge(_ENTAIL_PROMPT.format(context=ctx, claim=claim), model, max_tokens=10)
        if reply.lower().startswith("yes"):
            supported += 1
    return supported / len(claims)


# ---------- metric 2: answer relevance ------------------------------------
# Generate N questions the answer could be answering; cosine similarity vs real question.

_REVERSE_Q_PROMPT = """Given the ANSWER, generate {n} plausible questions it could be answering.
One question per line. No numbering, no preamble.

ANSWER: {answer}

Questions:"""


def _embed(texts: list[str]) -> np.ndarray:
    """Use voyage-3 embeddings if VOYAGE_API_KEY is set, else fall back to a bag-of-words
    cosine — good enough for ranking, not for absolute thresholds."""
    import os
    if os.environ.get("VOYAGE_API_KEY"):
        import voyageai
        vo = voyageai.Client()
        emb = np.array(vo.embed(texts, model="voyage-3", input_type="query").embeddings)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9
        return emb
    # bag-of-words fallback
    vocab: dict[str, int] = {}
    for t in texts:
        for tok in t.lower().split():
            vocab.setdefault(tok, len(vocab))
    M = np.zeros((len(texts), len(vocab)))
    for i, t in enumerate(texts):
        for tok in t.lower().split():
            M[i, vocab[tok]] += 1
    M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
    return M


def _answer_relevance_one(question: str, answer: str, model: str, n: int = 3) -> float:
    raw = _judge(_REVERSE_Q_PROMPT.format(n=n, answer=answer), model, max_tokens=300)
    generated = [line.strip() for line in raw.splitlines() if line.strip()][:n]
    if not generated:
        return 0.0
    emb = _embed([question] + generated)
    sims = emb[0] @ emb[1:].T
    return float(sims.mean())


# ---------- metric 3: context precision -----------------------------------
# For each retrieved chunk in rank order: is it relevant to the question?
# MAP-style: precision@k weighted by rank, where relevance is LLM-judged.

_CTX_REL_PROMPT = """Is the CONTEXT useful for answering the QUESTION?
Reply with exactly one word: yes or no.

QUESTION: {question}

CONTEXT: {ctx}

Answer:"""


def _context_precision_one(question: str, context: list[str], model: str) -> float:
    if not context:
        return 0.0
    rel = []
    for ctx in context:
        r = _judge(_CTX_REL_PROMPT.format(question=question, ctx=ctx), model, max_tokens=10)
        rel.append(1 if r.lower().startswith("yes") else 0)
    # weighted precision@k (Ragas definition): sum_k (precision@k * rel@k) / total_rel
    total_rel = sum(rel)
    if total_rel == 0:
        return 0.0
    weighted = 0.0
    for k in range(len(rel)):
        if rel[k]:
            precision_at_k = sum(rel[: k + 1]) / (k + 1)
            weighted += precision_at_k
    return weighted / total_rel


# ---------- metric 4: context recall --------------------------------------
# Decompose ground truth into atomic claims; fraction of gt claims supported by context.

_GT_CLAIM_PROMPT = """Extract atomic factual claims from the GROUND TRUTH. One per line, no numbering.

GROUND TRUTH: {gt}

Claims:"""


def _context_recall_one(ground_truth: str, context: list[str], model: str) -> float:
    raw = _judge(_GT_CLAIM_PROMPT.format(gt=ground_truth), model, max_tokens=500)
    claims = [re.sub(r"^[\d.\-)\s]+", "", line).strip()
              for line in raw.splitlines() if line.strip()]
    if not claims:
        return 1.0
    ctx = "\n\n".join(context)
    supported = 0
    for claim in claims:
        r = _judge(_ENTAIL_PROMPT.format(context=ctx, claim=claim), model, max_tokens=10)
        if r.lower().startswith("yes"):
            supported += 1
    return supported / len(claims)


# ---------- public entry point --------------------------------------------

def evaluate(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
    judge_model: str = "claude-sonnet-4-6",
) -> RagasResult:
    """Evaluate a RAG pipeline on N examples. All four lists must be same length.

    questions[i]     — user query
    answers[i]       — generator output
    contexts[i]      — retrieved chunks for example i (ordered by rank)
    ground_truths[i] — reference answer for recall

    Returns RagasResult with mean of each metric across the N examples.
    """
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths), \
        "questions, answers, contexts, ground_truths must align"
    n = len(questions)
    faith, relv, cprec, crec = [], [], [], []
    for i in range(n):
        faith.append(_faithfulness_one(answers[i], contexts[i], judge_model))
        relv.append(_answer_relevance_one(questions[i], answers[i], judge_model))
        cprec.append(_context_precision_one(questions[i], contexts[i], judge_model))
        crec.append(_context_recall_one(ground_truths[i], contexts[i], judge_model))
    return RagasResult(
        faithfulness=float(np.mean(faith)),
        answer_relevance=float(np.mean(relv)),
        context_precision=float(np.mean(cprec)),
        context_recall=float(np.mean(crec)),
    )


if __name__ == "__main__":
    # Smoke test — one example demonstrating all four metrics.
    q = "What scaling law governs compute-optimal LLM training?"
    a = ("Chinchilla scaling laws show that for a fixed compute budget, model size and "
         "training tokens should scale equally. A 70B model trained on 1.4T tokens matches "
         "a 280B model trained on 300B tokens.")
    ctx = ["Training Compute-Optimal Large Language Models (Chinchilla). We find that "
           "for compute-optimal training, model size and number of training tokens should "
           "be scaled equally: for every doubling of model size the number of training "
           "tokens should also be doubled."]
    gt = "Chinchilla: model size and training tokens should scale equally with compute."
    r = evaluate([q], [a], [ctx], [gt])
    print(json.dumps(r.as_dict(), indent=2))
