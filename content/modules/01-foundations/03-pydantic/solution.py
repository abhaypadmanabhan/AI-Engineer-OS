"""Classification schema + a stubbed 'LLM' that returns cached JSON strings."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ValidationError, field_validator


class Classification(BaseModel):
    category: Literal["billing", "bug", "feature", "spam"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(min_length=10, max_length=500)

    @field_validator("category", mode="before")
    @classmethod
    def normalize(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


def try_parse(raw: str) -> Classification | None:
    try:
        return Classification.model_validate_json(raw)
    except ValidationError:
        return None


# A valid payload plus 20 flavors of malformed output a real LLM will hand you.
VALID = '{"category":"Bug ","confidence":0.92,"reasoning":"Null pointer in user.py at line 42 of the login handler"}'

MALFORMED = [
    '{"category":"urgent","confidence":0.9,"reasoning":"not in literal set xxxxx"}',
    '{"category":"bug","confidence":1.4,"reasoning":"confidence out of range"}',
    '{"category":"bug","confidence":-0.1,"reasoning":"confidence negative xxxx"}',
    '{"category":"bug","confidence":0.9}',
    '{"confidence":0.9,"reasoning":"missing category xxxxxxxxxxx"}',
    '{"category":"bug","reasoning":"missing confidence xxxxxxxxx"}',
    '{"category":"bug","confidence":"high","reasoning":"string for number xxx"}',
    '{"category":42,"confidence":0.9,"reasoning":"int for category xxxx"}',
    '{"category":"bug","confidence":0.9,"reasoning":"short"}',
    '{"category":"bug","confidence":0.9,"reasoning":"' + ("x" * 600) + '"}',
    'not even json',
    '',
    '{}',
    'null',
    '[]',
    '{"category":null,"confidence":0.9,"reasoning":"null category xxxxxxx"}',
    '{"category":"bug","confidence":null,"reasoning":"null confidence xxx"}',
    '{"category":"bug","confidence":0.9,"reasoning":null}',
    '{"category":"spam","confidence":0.5,"reasoning":"ok"}',
    '{"category":"bug","confidence":0.9,"reasoning":"fine",,}',
]


def reject_rate() -> float:
    n_rejected = sum(try_parse(s) is None for s in MALFORMED)
    return n_rejected / len(MALFORMED)


def accept_valid() -> bool:
    return try_parse(VALID) is not None


if __name__ == "__main__":
    print("valid accepted:", accept_valid())
    print(f"reject_rate: {reject_rate():.2f}")
