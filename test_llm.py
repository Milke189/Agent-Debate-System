"""Tests for the LLM client."""

import pytest

from agent_debate.config import DebateConfig


def test_config_defaults():
    config = DebateConfig()
    assert config.debate_rounds == 2
    assert config.max_tokens == 4096
    assert config.temperature == 0.7
    assert "claude" in config.model


def test_config_custom():
    config = DebateConfig(debate_rounds=5, temperature=0.3)
    assert config.debate_rounds == 5
    assert config.temperature == 0.3
