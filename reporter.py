"""Generate Markdown debate reports."""

from __future__ import annotations

from datetime import datetime

from agent_debate.message import AGENT_DISPLAY, DebatePhase, DebateResult


def generate_report(result: DebateResult) -> str:
    sections = [
        f"# Agent Debate Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Problem",
        result.problem,
        "",
    ]

    # Independent Analyses
    sections.append("## Independent Analyses\n")
    for analysis in result.independent_analyses:
        label, _ = AGENT_DISPLAY.get(analysis.role, (analysis.role.value, ""))
        sections.append(f"### {label}\n")
        sections.append(analysis.analysis)
        if analysis.key_findings:
            sections.append("\n**Key Findings:**")
            for f in analysis.key_findings:
                sections.append(f"- {f}")
        if analysis.concerns:
            sections.append("\n**Concerns:**")
            for c in analysis.concerns:
                sections.append(f"- {c}")
        if analysis.recommendations:
            sections.append("\n**Recommendations:**")
            for r in analysis.recommendations:
                sections.append(f"- {r}")
        sections.append("")

    # Debate Highlights
    cross_msgs = [m for m in result.messages if m.phase == DebatePhase.CROSS_EXAMINATION]
    if cross_msgs:
        sections.append("## Cross-Examination Highlights\n")
        for msg in cross_msgs:
            label, _ = AGENT_DISPLAY.get(msg.sender, (msg.sender.value, ""))
            sections.append(f"**{label}** (Round {msg.round}):\n")
            sections.append(msg.content)
            sections.append("")

    rebuttal_msgs = [m for m in result.messages if m.phase == DebatePhase.REBUTTAL]
    if rebuttal_msgs:
        sections.append("## Rebuttals\n")
        for msg in rebuttal_msgs:
            label, _ = AGENT_DISPLAY.get(msg.sender, (msg.sender.value, ""))
            sections.append(f"**{label}** (Round {msg.round}):\n")
            sections.append(msg.content)
            sections.append("")

    # Consensus
    sections.append("## Consensus\n")
    sections.append(result.consensus_summary)
    sections.append("")

    # Stats
    total = len(result.messages)
    sections.append(f"---\n\n*Total messages in debate: {total}*")

    return "\n".join(sections)
