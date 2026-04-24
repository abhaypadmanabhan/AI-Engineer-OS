"""Solution: measure time-to-first-token across 5 runs; report median ms."""
import os
import time
import statistics
from anthropic import Anthropic


def ttft_ms(client: Anthropic) -> float:
    t0 = time.perf_counter()
    first = None
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": "Say hi in one sentence."}],
    ) as s:
        for text in s.text_stream:
            if text.strip():
                first = time.perf_counter()
                break
    assert first is not None, "never received a token"
    return (first - t0) * 1000.0


def main() -> None:
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    client = Anthropic()
    samples = [ttft_ms(client) for _ in range(5)]
    median = statistics.median(samples)
    print(f"samples_ms={[round(s) for s in samples]}")
    print(f"median_ms={median:.0f}")


if __name__ == "__main__":
    main()
