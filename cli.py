"""CLI interface for the Agent Debate System."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

from agent_debate.agent import create_agents
from agent_debate.config import DebateConfig
from agent_debate.llm import LLMClient
from agent_debate.message import AGENT_DISPLAY, AgentRole, DebatePhase, Message
from agent_debate.orchestrator import DebateOrchestrator
from agent_debate.reporter import generate_report

custom_theme = Theme({
    "security": "red",
    "performance": "yellow",
    "ux": "green",
    "architecture": "blue",
    "moderator": "magenta",
    "phase": "cyan bold",
})

console = Console(theme=custom_theme)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent-debate",
        description="Multi-Agent collaborative debate system for code review",
    )
    parser.add_argument(
        "problem",
        nargs="?",
        help="Problem or code to review (or use -f for file input)",
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Read problem from file",
    )
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=2,
        help="Number of debate rounds (default: 2)",
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Save report to file",
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=["security", "performance", "ux", "architecture", "moderator"],
        default=["security", "performance", "ux", "architecture", "moderator"],
        help="Which agents to include (default: all 5)",
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output with token usage",
    )
    return parser.parse_args()


def read_problem(args: argparse.Namespace) -> str:
    if args.file:
        return args.file.read_text(encoding="utf-8")
    if args.problem:
        return args.problem
    if not sys.stdin.isatty():
        return sys.stdin.read()
    console.print("[red]Error:[/red] Provide a problem via argument, -f flag, or stdin")
    sys.exit(1)


def print_phase_banner(phase: str) -> None:
    console.print()
    console.rule(f"[phase]{phase}")


def print_message(msg: Message) -> None:
    label, color = AGENT_DISPLAY.get(msg.sender, (msg.sender.value, "white"))
    console.print()
    console.print(
        Panel(
            Markdown(msg.content),
            title=f"[{color}]{label}[/{color}]",
            title_align="left",
            border_style=color,
            padding=(1, 2),
        )
    )


async def on_phase_callback(phase: str, messages: list[Message]) -> None:
    print_phase_banner(phase)
    for msg in messages:
        print_message(msg)


async def async_main(args: argparse.Namespace) -> None:
    problem = read_problem(args)

    config = DebateConfig(
        model=args.model,
        debate_rounds=args.rounds,
    )

    roles = [AgentRole(r) for r in args.agents]
    llm = LLMClient(config, api_key=args.api_key)
    agents = create_agents(llm, roles)

    console.print(Panel(
        f"[bold]Problem:[/bold]\n{problem[:200]}{'...' if len(problem) > 200 else ''}\n\n"
        f"[bold]Agents:[/bold] {', '.join(args.agents)}\n"
        f"[bold]Rounds:[/bold] {args.rounds}\n"
        f"[bold]Model:[/bold] {args.model}",
        title="Agent Debate System",
        border_style="cyan",
    ))

    orchestrator = DebateOrchestrator(agents, config, on_phase=on_phase_callback)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running debate...", total=None)
        result = await orchestrator.run(problem)
        progress.update(task, completed=True)

    # Print consensus summary
    print_phase_banner("Final Consensus")
    console.print(Markdown(result.consensus_summary))

    # Token usage
    if args.verbose:
        console.print(f"\n[dim]{llm.usage_summary()}[/dim]")

    # Save report
    if args.output:
        report = generate_report(result)
        args.output.write_text(report, encoding="utf-8")
        console.print(f"\n[green]Report saved to {args.output}[/green]")


def main() -> None:
    args = parse_args()
    asyncio.run(async_main(args))
