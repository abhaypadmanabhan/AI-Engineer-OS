"""Ragas harness — faithfulness, answer_relevance, context_precision, context_recall.

PRIMARY PATH: the `ragas` library with an Anthropic-backed judge + Cohere embeddings.
This is the exact signature 3.10 (L3 mastery gate) and Capstone M2 import — no
teaching wrappers on the primary path.

TEACHING HELPERS: `demo_faithfulness` and `demo_context_precision` show the raw
math — claim extraction + entailment, LLM-judged weighted precision@k. The lab
uses them to unpack what ragas is doing under the hood; production code imports
`evaluate` only.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

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


# ---------- PRIMARY PATH: ragas library -----------------------------------

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

    Returns RagasResult (means across N examples).
    """
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths), \
        "questions, answers, contexts, ground_truths must align"

    from ragas import EvaluationDataset, SingleTurnSample
    from ragas import evaluate as _ragas_evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )
    from langchain_anthropic import ChatAnthropic
    from langchain_cohere import CohereEmbeddings

    llm = LangchainLLMWrapper(
        ChatAnthropic(model=judge_model, temperature=0, max_tokens=1024)
    )
    embeddings = LangchainEmbeddingsWrapper(CohereEmbeddings(model="embed-english-v3.0"))

    samples = [
        SingleTurnSample(
            user_input=q, response=a, retrieved_contexts=list(c), reference=g,
        )
        for q, a, c, g in zip(questions, answers, contexts, ground_truths)
    ]
    dataset = EvaluationDataset(samples=samples)

    faith_m = Faithfulness()
    relv_m = ResponseRelevancy()
    cprec_m = LLMContextPrecisionWithReference()
    crec_m = LLMContextRecall()

    result = _ragas_evaluate(
        dataset=dataset,
        metrics=[faith_m, relv_m, cprec_m, crec_m],
        llm=llm,
        embeddings=embeddings,
    )
    df = result.to_pandas()

    def _mean(metric_name: str) -> float:
        return float(df[metric_name].dropna().mean())

    return RagasResult(
        faithfulness=_mean(faith_m.name),
        answer_relevance=_mean(relv_m.name),
        context_precision=_mean(cprec_m.name),
        context_recall=_mean(crec_m.name),
    )


# ---------- TEACHING HELPERS (used by the lab's "Under the hood" cells) ---
# Not on the production path. Show the math ragas runs internally.

_ENTAIL_PROMPT = """Is the CLAIM supported by the CONTEXT? Reply with exactly one word: yes or no.

CONTEXT:
{context}

CLAIM: {claim}

Answer:"""

_CLAIM_PROMPT = """Extract atomic factual claims from the answer. One claim per line, no numbering.
Skip opinions, questions, and meta-commentary. Only verifiable factual statements.

Answer: {answer}

Claims:"""

_CTX_REL_PROMPT = """Is the CONTEXT useful for answering the QUESTION?
Reply with exactly one word: yes or no.

QUESTION: {question}

CONTEXT: {ctx}

Answer:"""


def _judge(prompt: str, model: str, max_tokens: int = 800) -> str:
    r = _client.messages.create(
        model=model, max_tokens=max_tokens, temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()


def demo_faithfulness(answer: str, context: list[str], judge_model: str = "claude-sonnet-4-6") -> float:
    """Teaching demo: extract atomic claims, NLI each against the joined context.
    This is what ragas.Faithfulness does internally (with a more detailed prompt)."""
    raw = _judge(_CLAIM_PROMPT.format(answer=answer), judge_model, max_tokens=500)
    claims = [re.sub(r"^[\d.\-)\s]+", "", line).strip()
              for line in raw.splitlines() if line.strip()]
    if not claims:
        return 1.0
    ctx = "\n\n".join(context)
    supported = sum(
        1 for c in claims
        if _judge(_ENTAIL_PROMPT.format(context=ctx, claim=c), judge_model, 10)
           .lower().startswith("yes")
    )
    return supported / len(claims)


def demo_context_precision(
    question: str, context: list[str], judge_model: str = "claude-sonnet-4-6",
) -> float:
    """Teaching demo: LLM-judge per-chunk relevance, weighted precision@k over ranks.
    This is the shape of ragas.LLMContextPrecisionWithReference internally."""
    if not context:
        return 0.0
    rel = [
        1 if _judge(_CTX_REL_PROMPT.format(question=question, ctx=c), judge_model, 10)
             .lower().startswith("yes") else 0
        for c in context
    ]
    total = sum(rel)
    if total == 0:
        return 0.0
    weighted = sum(
        (sum(rel[: k + 1]) / (k + 1)) for k in range(len(rel)) if rel[k]
    )
    return weighted / total


if __name__ == "__main__":
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
