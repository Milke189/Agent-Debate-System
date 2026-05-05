"""Tests for the reporter."""

from agent_debate.message import AgentRole, DebatePhase, Message
from agent_debate.message import AgentAnalysis, DebateResult
from agent_debate.reporter import generate_report


def test_generate_report():
    result = DebateResult(
        problem="def foo(): pass",
        independent_analyses=[
            AgentAnalysis(
                role=AgentRole.SECURITY,
                analysis="Looks fine.",
                key_findings=["No issues"],
                concerns=[],
                recommendations=["Add auth"],
            ),
        ],
        consensus_summary="### Consensus\nAll agree the code is acceptable.",
        messages=[
            Message(
                sender=AgentRole.SECURITY,
                phase=DebatePhase.INDEPENDENT_ANALYSIS,
                content="Looks fine.",
            ),
            Message(
                sender=AgentRole.MODERATOR,
                phase=DebatePhase.CONSENSUS,
                content="All agree.",
            ),
        ],
    )

    report = generate_report(result)

    assert "Agent Debate Report" in report
    assert "def foo(): pass" in report
    assert "Security" in report
    assert "Consensus" in report
    assert "Total messages in debate: 2" in report
