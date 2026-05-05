"""Configuration for the debate system."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DebateConfig(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    debate_rounds: int = 2
    temperature: float = 0.7
    enable_streaming: bool = False
