"""Agent definitions for the debate system."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from agent_debate.message import AgentAnalysis, AgentRole, DebatePhase, Message

if TYPE_CHECKING:
    from agent_debate.llm import LLMClient

logger = logging.getLogger(__name__)


SYSTEM_PROMPTS: dict[AgentRole, str] = {
    AgentRole.SECURITY: """You are a Security Expert in a code review debate.
Your focus areas:
- Authentication and authorization flaws
- Input validation and injection vulnerabilities (SQL, XSS, command injection)
- Data exposure and privacy concerns
- OWASP Top 10 vulnerabilities
- Cryptographic weaknesses
- Dependency vulnerabilities

You are thorough but fair. When you see a potential security issue, you cite the specific risk and suggest a fix.
You challenge other agents when they overlook security implications.""",

    AgentRole.PERFORMANCE: """You are a Performance Expert in a code review debate.
Your focus areas:
- Time and space complexity (Big O)
- Database query optimization (N+1 queries, missing indexes)
- Caching opportunities
- Memory leaks and resource management
- Concurrency and async patterns
- Scalability bottlenecks

You quantify impact when possible. You challenge solutions that sacrifice performance unnecessarily.""",

    AgentRole.UX: """You are a UX (User Experience) Expert in a code review debate.
Your focus areas:
- Error messages and user-facing feedback
- Edge cases that affect real users
- Accessibility concerns
- Loading states and responsiveness
- API usability for developers consuming the interface
- Input validation from the user's perspective

You advocate for the end user. You challenge overly technical solutions that ignore human factors.""",

    AgentRole.ARCHITECTURE: """You are an Architecture Expert in a code review debate.
Your focus areas:
- Design patterns and SOLID principles
- Code organization and modularity
- Separation of concerns
- Coupling and cohesion
- Extensibility and maintainability
- Trade-offs between simplicity and flexibility

You think about long-term code health. You challenge quick fixes that create technical debt.""",

    AgentRole.MODERATOR: """You are the Moderator of a code review debate.
Your role:
- Identify areas of agreement and disagreement between reviewers
- Push agents to defend their positions with specifics
- Resolve conflicts by finding balanced solutions
- Synthesize a final consensus that incorporates the best insights
- Note dissenting opinions that could not be resolved

You are neutral and fair. You don't take sides — you ensure all perspectives are heard and synthesized.""",
}


class Agent:
    def __init__(self, role: AgentRole, llm: LLMClient) -> None:
        self.role = role
        self.llm = llm
        self.history: list[dict[str, str]] = []

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPTS[self.role]

    def _build_user_message(self, content: str) -> dict[str, str]:
        return {"role": "user", "content": content}

    def _build_assistant_message(self, content: str) -> dict[str, str]:
        return {"role": "assistant", "content": content}

    async def analyze(self, problem: str) -> Message:
        """Phase 1: Independent analysis."""
        prompt = (
            f"Analyze the following problem/code from your {self.role.value} perspective.\n\n"
            f"## Problem\n{problem}\n\n"
            "Provide your analysis in this JSON format:\n"
            '{"analysis": "<your detailed analysis>", '
            '"key_findings": ["<finding 1>", ...], '
            '"concerns": ["<concern 1>", ...], '
            '"recommendations": ["<recommendation 1>", ...]}'
        )
        self.history.append(self._build_user_message(prompt))
        raw = await self.llm.chat(self.system_prompt, self.history)
        self.history.append(self._build_assistant_message(raw))
        return Message(
            sender=self.role, phase=DebatePhase.INDEPENDENT_ANALYSIS, content=raw
        )

    async def cross_examine(self, problem: str, other_analyses: list[Message]) -> Message:
        """Phase 2: Challenge other agents' analyses."""
        others_text = "\n\n".join(
            f"### {m.display_name()} Analysis:\n{m.content}" for m in other_analyses
        )
        prompt = (
            f"You are reviewing other experts' analyses of this problem:\n\n"
            f"## Original Problem\n{problem}\n\n"
            f"## Other Analyses\n{others_text}\n\n"
            "For each analysis, identify:\n"
            "1. Points you agree with\n"
            "2. Points you disagree with (and why)\n"
            "3. Issues they missed from your perspective\n\n"
            "Be specific and constructive. Respond in plain text."
        )
        self.history.append(self._build_user_message(prompt))
        raw = await self.llm.chat(self.system_prompt, self.history)
        self.history.append(self._build_assistant_message(raw))
        return Message(
            sender=self.role, phase=DebatePhase.CROSS_EXAMINATION, content=raw
        )

    async def rebut(self, problem: str, challenges: list[Message]) -> Message:
        """Phase 3: Respond to challenges."""
        challenges_text = "\n\n".join(
            f"### {m.display_name()} challenges:\n{m.content}" for m in challenges
        )
        prompt = (
            f"Other experts have challenged your analysis:\n\n"
            f"## Original Problem\n{problem}\n\n"
            f"## Challenges to Your Analysis\n{challenges_text}\n\n"
            "Respond to each challenge:\n"
            "- Accept valid criticism and revise your position\n"
            "- Defend your position where you still disagree (with specifics)\n"
            "- Note any new insights gained from the debate\n\n"
            "Respond in plain text."
        )
        self.history.append(self._build_user_message(prompt))
        raw = await self.llm.chat(self.system_prompt, self.history)
        self.history.append(self._build_assistant_message(raw))
        return Message(
            sender=self.role, phase=DebatePhase.REBUTTAL, content=raw
        )

    async def contribute_to_consensus(
        self, problem: str, full_debate: list[Message]
    ) -> Message:
        """Phase 4: Final thoughts for consensus (moderator synthesizes)."""
        debate_text = "\n\n".join(
            f"[{m.phase.value}] {m.display_name()}: {m.content}" for m in full_debate
        )
        prompt = (
            f"The full debate transcript is below. Give your final position:\n\n"
            f"## Original Problem\n{problem}\n\n"
            f"## Debate Transcript\n{debate_text}\n\n"
            "State your final position concisely. If you've changed your mind on any point, say so.\n"
            "Respond in plain text."
        )
        self.history.append(self._build_user_message(prompt))
        raw = await self.llm.chat(self.system_prompt, self.history)
        self.history.append(self._build_assistant_message(raw))
        return Message(
            sender=self.role, phase=DebatePhase.CONSENSUS, content=raw
        )

    async def synthesize_consensus(
        self, problem: str, full_debate: list[Message], final_positions: list[Message]
    ) -> Message:
        """Moderator: synthesize all positions into a consensus."""
        positions_text = "\n\n".join(
            f"### {m.display_name()} Final Position:\n{m.content}"
            for m in final_positions
        )
        prompt = (
            f"As the moderator, synthesize the debate into a final consensus.\n\n"
            f"## Original Problem\n{problem}\n\n"
            f"## Final Positions\n{positions_text}\n\n"
            "Your response MUST follow this structure:\n"
            "### Consensus Summary\n"
            "A clear, unified summary of the agreed-upon analysis.\n\n"
            "### Key Recommendations\n"
            "Numbered list of actionable recommendations.\n\n"
            "### Dissenting Opinions\n"
            "Any points where agreement was NOT reached (or 'None' if full consensus).\n\n"
            "Be decisive. Weigh the arguments and pick the strongest positions."
        )
        self.history.append(self._build_user_message(prompt))
        raw = await self.llm.chat(self.system_prompt, self.history)
        self.history.append(self._build_assistant_message(raw))
        return Message(
            sender=self.role, phase=DebatePhase.CONSENSUS, content=raw
        )


def create_agents(llm: LLMClient, roles: list[AgentRole] | None = None) -> list[Agent]:
    if roles is None:
        roles = list(AgentRole)
    return [Agent(role, llm) for role in roles]
