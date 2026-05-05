"""Debate orchestrator — manages the multi-phase debate flow."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Awaitable

from agent_debate.message import AgentRole, DebatePhase, DebateResult, Message

if TYPE_CHECKING:
    from agent_debate.agent import Agent
    from agent_debate.config import DebateConfig

logger = logging.getLogger(__name__)

PhaseCallback = Callable[[str, list[Message]], Awaitable[None]]


class DebateOrchestrator:
    def __init__(
        self,
        agents: list[Agent],
        config: DebateConfig,
        on_phase: PhaseCallback | None = None,
    ) -> None:
        self.agents = agents
        self.config = config
        self.on_phase = on_phase
        self.result = DebateResult(problem="")
        self._moderator = next(a for a in agents if a.role == AgentRole.MODERATOR)
        self._experts = [a for a in agents if a.role != AgentRole.MODERATOR]

    async def _notify_phase(self, phase: str, messages: list[Message]) -> None:
        if self.on_phase:
            await self.on_phase(phase, messages)

    async def run(self, problem: str) -> DebateResult:
        self.result.problem = problem
        logger.info("Starting debate with %d agents", len(self.agents))

        # Phase 1: Independent analysis (parallel)
        logger.info("Phase 1: Independent Analysis")
        analyses = await self._phase_independent_analysis(problem)
        self.result.independent_analyses = [
            a for a in [
                self._parse_analysis(m) for m in analyses
            ] if a is not None
        ]

        # Phase 2-N: Cross-examination rounds
        for round_num in range(1, self.config.debate_rounds + 1):
            logger.info("Phase 2: Cross-Examination (round %d)", round_num)
            await self._phase_cross_examination(problem, analyses, round_num)

            logger.info("Phase 3: Rebuttal (round %d)", round_num)
            await self._phase_rebuttal(problem, round_num)

        # Final phase: Consensus
        logger.info("Phase 4: Consensus Building")
        await self._phase_consensus(problem)

        return self.result

    async def _phase_independent_analysis(self, problem: str) -> list[Message]:
        tasks = [agent.analyze(problem) for agent in self.expert_agents()]
        messages = await asyncio.gather(*tasks)
        self.result.messages.extend(messages)
        await self._notify_phase("Independent Analysis", list(messages))
        return list(messages)

    async def _phase_cross_examination(
        self, problem: str, analyses: list[Message], round_num: int
    ) -> None:
        # Each expert cross-examines all other experts
        tasks = []
        for agent in self._experts:
            others = [m for m in analyses if m.sender != agent.role]
            tasks.append(agent.cross_examine(problem, others))

        messages = await asyncio.gather(*tasks)
        # Tag with round number
        for m in messages:
            m.round = round_num
        self.result.messages.extend(messages)
        await self._notify_phase("Cross-Examination", list(messages))

    async def _phase_rebuttal(self, problem: str, round_num: int) -> None:
        # Each expert rebuts challenges directed at them
        cross_exam_msgs = [
            m for m in self.result.messages
            if m.phase == DebatePhase.CROSS_EXAMINATION and m.round == round_num
        ]

        tasks = []
        for agent in self._experts:
            # Challenges from others (not from this agent)
            challenges = [m for m in cross_exam_msgs if m.sender != agent.role]
            tasks.append(agent.rebut(problem, challenges))

        messages = await asyncio.gather(*tasks)
        for m in messages:
            m.round = round_num
        self.result.messages.extend(messages)
        await self._notify_phase("Rebuttal", list(messages))

    async def _phase_consensus(self, problem: str) -> None:
        full_debate = list(self.result.messages)

        # All agents give final position
        tasks = [
            agent.contribute_to_consensus(problem, full_debate)
            for agent in self._experts
        ]
        final_positions = await asyncio.gather(*tasks)
        self.result.messages.extend(final_positions)

        # Moderator synthesizes consensus
        consensus = await self._moderator.synthesize_consensus(
            problem, full_debate, list(final_positions)
        )
        self.result.messages.append(consensus)
        self.result.consensus_summary = consensus.content
        await self._notify_phase("Consensus", [consensus])

    def expert_agents(self) -> list[Agent]:
        return list(self._experts)

    def _parse_analysis(self, msg: Message) -> "AgentAnalysis | None":
        """Best-effort parse of the JSON analysis block."""
        from agent_debate.message import AgentAnalysis
        import json

        try:
            # Try to find JSON in the response
            text = msg.content
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return AgentAnalysis(
                    role=msg.sender,
                    analysis=data.get("analysis", text),
                    key_findings=data.get("key_findings", []),
                    concerns=data.get("concerns", []),
                    recommendations=data.get("recommendations", []),
                )
        except (json.JSONDecodeError, KeyError):
            pass
        return AgentAnalysis(
            role=msg.sender, analysis=msg.content,
            key_findings=[], concerns=[], recommendations=[],
        )
