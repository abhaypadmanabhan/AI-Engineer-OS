"""Solution: one-token completion to prove the autoregressive loop."""
import os
from anthropic import Anthropic


def next_token(prompt: str) -> str:
    client = Anthropic()
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text


if __name__ == "__main__":
    assert os.environ.get("ANTHROPIC_API_KEY"), "set ANTHROPIC_API_KEY"
    out = next_token("The capital of France is")
    print(repr(out))
    assert "Paris" in out, f"unexpected: {out!r}"
    print("ok")
