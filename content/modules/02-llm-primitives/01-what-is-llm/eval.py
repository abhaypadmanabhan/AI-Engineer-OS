"""Eval: gate passes if learner can produce a one-sentence definition
containing the three core terms. Checked lexically, not semantically."""
import sys

SENTENCE = sys.argv[1] if len(sys.argv) > 1 else ""
required = ["token", "probab", "autoreg"]  # stems tolerate variants
hits = sum(1 for r in required if r.lower() in SENTENCE.lower())
score = 1 if hits == 3 else 0
print(f"score={score} hits={hits}/3")
sys.exit(0 if score >= 1 else 1)
