"""Claude API wrapper with retry logic."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import anthropic

from agent_debate.config import DebateConfig

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: DebateConfig, api_key: str | None = None) -> None:
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        retries = 3
        for attempt in range(retries):
            try:
                resp = await self.client.messages.create(
                    model=self.config.model,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=temperature or self.config.temperature,
                    system=system_prompt,
                    messages=messages,
                )
                self.total_input_tokens += resp.usage.input_tokens
                self.total_output_tokens += resp.usage.output_tokens
                return resp.content[0].text
            except (
                anthropic.RateLimitError,
                anthropic.APIConnectionError,
                anthropic.InternalServerError,
            ) as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** (attempt + 1)
                logger.warning("API error (%s), retrying in %ds...", e, wait)
                await asyncio.sleep(wait)
        raise RuntimeError("Unreachable")

    def usage_summary(self) -> str:
        return (
            f"Tokens used — input: {self.total_input_tokens:,}, "
            f"output: {self.total_output_tokens:,}"
        )
