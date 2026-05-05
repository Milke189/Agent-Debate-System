"""Tests for the agent system."""

import pytest

from agent_debate.agent import Agent, SYSTEM_PROMPTS, create_agents
from agent_debate.message import AgentRole, DebatePhase


class FakeLLM:
    """Minimal mock LLM for testing."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = responses or []
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def chat(self, system_prompt: str, messages: list[dict], **kwargs) -> str:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
        else:
            resp = '{"analysis": "test", "key_findings": [], "concerns": [], "recommendations": []}'
        self.call_count += 1
        return resp

    def usage_summary(self) -> str:
        return "test usage"


@pytest.mark.asyncio
async def test_agent_analyze():
    llm = FakeLLM([
        '{"analysis": "Looks secure", "key_findings": ["No SQL injection"], "concerns": [], "recommendations": ["Add HTTPS"]}'
    ])
    agent = Agent(AgentRole.SECURITY, llm)
    msg = await agent.analyze("def foo(): pass")

    assert msg.sender == AgentRole.SECURITY
    assert msg.phase == DebatePhase.INDEPENDENT_ANALYSIS
    assert "Looks secure" in msg.content
    assert llm.call_count == 1


@pytest.mark.asyncio
async def test_agent_cross_examine():
    llm = FakeLLM(["I agree with security but performance is overlooked."])
    agent = Agent(AgentRole.PERFORMANCE, llm)

    from agent_debate.message import Message
    other = Message(
        sender=AgentRole.SECURITY,
        phase=DebatePhase.INDEPENDENT_ANALYSIS,
        content="No issues found.",
    )
    msg = await agent.cross_examine("def foo(): pass", [other])

    assert msg.sender == AgentRole.PERFORMANCE
    assert msg.phase == DebatePhase.CROSS_EXAMINATION


@pytest.mark.asyncio
async def test_agent_rebut():
    llm = FakeLLM(["I accept the point about caching."])
    agent = Agent(AgentRole.UX, llm)

    from agent_debate.message import Message
    challenge = Message(
        sender=AgentRole.PERFORMANCE,
        phase=DebatePhase.CROSS_EXAMINATION,
        content="UX didn't consider loading states.",
    )
    msg = await agent.rebut("def foo(): pass", [challenge])

    assert msg.phase == DebatePhase.REBUTTAL


@pytest.mark.asyncio
async def test_synthesize_consensus():
    llm = FakeLLM([
        "### Consensus Summary\nAll agents agree the code is solid.\n\n### Key Recommendations\n1. Add HTTPS\n\n### Dissenting Opinions\nNone"
    ])
    agent = Agent(AgentRole.MODERATOR, llm)

    from agent_debate.message import Message
    positions = [
        Message(sender=AgentRole.SECURITY, phase=DebatePhase.CONSENSUS, content="Looks good."),
    ]
    msg = await agent.synthesize_consensus("def foo(): pass", [], positions)

    assert msg.sender == AgentRole.MODERATOR
    assert "Consensus Summary" in msg.content


def test_system_prompts_exist():
    for role in AgentRole:
        assert role in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS[role]) > 50


def test_create_agents_default():
    llm = FakeLLM()
    agents = create_agents(llm)
    assert len(agents) == 5
    roles = {a.role for a in agents}
    assert roles == set(AgentRole)


def test_create_agents_subset():
    llm = FakeLLM()
    agents = create_agents(llm, [AgentRole.SECURITY, AgentRole.MODERATOR])
    assert len(agents) == 2
