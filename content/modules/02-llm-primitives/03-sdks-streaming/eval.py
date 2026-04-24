"""Eval: pass if median TTFT <= 600ms over 5 streaming runs."""
import os
import sys
import time
import statistics

THRESHOLD_MS = 600


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skip: ANTHROPIC_API_KEY not set")
        return 1
    from anthropic import Anthropic
    client = Anthropic()
    samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": "hi"}],
        ) as s:
            for text in s.text_stream:
                if text.strip():
                    samples.append((time.perf_counter() - t0) * 1000)
                    break
    median = statistics.median(samples)
    print(f"median_ttft_ms={median:.0f} threshold={THRESHOLD_MS}")
    return 0 if median <= THRESHOLD_MS else 1


if __name__ == "__main__":
    sys.exit(main())
