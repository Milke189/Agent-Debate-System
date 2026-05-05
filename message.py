"""Data models for the debate system."""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field


class AgentRole(str, enum.Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    UX = "ux"
    ARCHITECTURE = "architecture"
    MODERATOR = "moderator"


class DebatePhase(str, enum.Enum):
    INDEPENDENT_ANALYSIS = "independent_analysis"
    CROSS_EXAMINATION = "cross_examination"
    REBUTTAL = "rebuttal"
    CONSENSUS = "consensus"


AGENT_DISPLAY: dict[AgentRole, tuple[str, str]] = {
    AgentRole.SECURITY: ("🛡️  Security", "red"),
    AgentRole.PERFORMANCE: ("⚡ Performance", "yellow"),
    AgentRole.UX: ("👤 UX", "green"),
    AgentRole.ARCHITECTURE: ("🏗️  Architecture", "blue"),
    AgentRole.MODERATOR: ("🎯 Moderator", "magenta"),
}


class Message(BaseModel):
    sender: AgentRole
    phase: DebatePhase
    round: int = 0
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    def display_name(self) -> str:
        label, _ = AGENT_DISPLAY.get(self.sender, (self.sender.value, "white"))
        return label

    def color(self) -> str:
        _, color = AGENT_DISPLAY.get(self.sender, (self.sender.value, "white"))
        return color


class AgentAnalysis(BaseModel):
    role: AgentRole
    analysis: str
    key_findings: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DebateResult(BaseModel):
    problem: str
    messages: list[Message] = Field(default_factory=list)
    independent_analyses: list[AgentAnalysis] = Field(default_factory=list)
    consensus_summary: str = ""
    dissenting_opinions: list[str] = Field(default_factory=list)
    actionable_recommendations: list[str] = Field(default_factory=list)
