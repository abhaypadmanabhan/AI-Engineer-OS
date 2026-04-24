"""Pydantic schemas for FilingSage M1 structured output.

These classes define the exact shape Claude must return via `tool_use`.
The JSON schema is derived with `FilingSummary.model_json_schema()` and
passed as the `input_schema` of the `submit_filing_summary` tool.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    category: Literal[
        "regulatory",
        "competitive",
        "operational",
        "financial",
        "macro",
        "cyber",
        "supply_chain",
        "other",
    ]
    summary: str = Field(max_length=280)
    severity: Literal["low", "mid", "high"]


class Segment(BaseModel):
    name: str
    revenue_usd_millions: float | None = None
    yoy_growth_pct: float | None = None


class FilingSummary(BaseModel):
    ticker: str
    fiscal_year_end: str  # YYYY-MM-DD
    accession_number: str  # SEC 18-digit accession
    top_risk_factors: list[RiskFactor] = Field(min_length=3, max_length=7)
    segments: list[Segment] = Field(max_length=10)
    management_outlook: str = Field(max_length=500)
    material_changes_vs_prior_year: list[str] = Field(max_length=5)
    citations: list[str] = Field(
        min_length=1,
        description="Section headings from the 10-K used (e.g., 'Item 1A', 'Item 7')",
    )
