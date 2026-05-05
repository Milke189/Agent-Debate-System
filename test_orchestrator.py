"""Tests for the debate orchestrator."""

import pytest

from agent_debate.agent import Agent
from agent_debate.config import DebateConfig
from agent_debate.message import AgentRole, DebatePhase
from agent_debate.orchestrator import DebateOrchestrator


class FakeLLM:
    """Returns a sequence of JSON-formatted responses."""

    def __init__(self) -> None:
        self.call_count = 0

    async def chat(self, system_prompt: str, messages: list[dict], **kwargs) -> str:
        self.call_count += 1
        return (
            '{"analysis": "Analysis from call '
            + str(self.call_count)
            + '", "key_findings": ["finding1"], "concerns": [], "recommendations": ["rec1"]}'
        )

    def usage_summary(self) -> str:
        return ""


@pytest.mark.asyncio
async def test_full_debate_runs():
    llm = FakeLLM()
    agents = [Agent(role, llm) for role in AgentRole]
    config = DebateConfig(debate_rounds=1)  # 1 round to keep it fast
    orchestrator = DebateOrchestrator(agents, config)

    result = await orchestrator.run("def foo(): return 42")

    assert result.problem == "def foo(): return 42"
    # Should have: 5 independent + 4 cross-exam + 4 rebuttal + 5 final positions + 1 consensus
    assert len(result.messages) > 0
    assert result.consensus_summary != ""
    assert llm.call_count > 5  # At least one call per agent per phase


@pytest.mark.asyncio
async def test_phase_callback():
    llm = FakeLLM()
    agents = [Agent(AgentRole.SECURITY, llm), Agent(AgentRole.MODERATOR, llm)]
    config = DebateConfig(debate_rounds=1)

    phases_seen: list[str] = []

    async def on_phase(phase: str, messages: list) -> None:
        phases_seen.append(phase)

    orchestrator = DebateOrchestrator(agents, config, on_phase=on_phase)
    await orchestrator.run("test problem")

    assert "Independent Analysis" in phases_seen
    assert "Consensus" in phases_seen


@pytest.mark.asyncio
async def test_independent_analyses_parsed():
    llm = FakeLLM()
    agents = [Agent(AgentRole.SECURITY, llm), Agent(AgentRole.MODERATOR, llm)]
    config = DebateConfig(debate_rounds=1)
    orchestrator = DebateOrchestrator(agents, config)

    result = await orchestrator.run("test")

    assert len(result.independent_analyses) >= 1
    for analysis in result.independent_analyses:
        assert analysis.role in AgentRole
