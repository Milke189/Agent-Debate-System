# Agent Debate System

Multi-Agent collaborative debate system for code review. Five specialized AI agents independently analyze your code, challenge each other's findings, debate through multiple rounds, and reach a consensus — simulating a real senior engineering team's code review process.

## How It Works

```
Problem In
    │
    ▼
┌─────────────────────────────────────────┐
│  Phase 1: Independent Analysis (async)  │
│  5 agents analyze concurrently          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phase 2: Cross-Examination             │
│  Each agent challenges others' analyses │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phase 3: Rebuttal                      │
│  Agents defend or revise positions      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phase 4: Consensus                     │
│  Moderator synthesizes final report     │
└────────────┬────────────────────────────┘
             │
             ▼
      Final Report
```

Phases 2-3 repeat for configurable rounds (default: 2), allowing deeper debate.

## The Agents

| Agent | Focus |
|---|---|
| **Security** | Auth flaws, injection, data exposure, OWASP Top 10 |
| **Performance** | Complexity, caching, N+1 queries, scalability |
| **UX** | Error messages, edge cases, accessibility, developer ergonomics |
| **Architecture** | Design patterns, SOLID, coupling, maintainability |
| **Moderator** | Facilitates debate, resolves conflicts, synthesizes consensus |

## Installation

```bash
git clone https://github.com/Milke189/agent-debate.git
cd agent-debate
pip install -e .
```

## Quick Start

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Review a code snippet
agent-debate "def login(u, p): return db.query(f'SELECT * FROM users WHERE name={u}')"

# Review a file
agent-debate -f src/app.py

# Pipe from stdin
cat problem.txt | agent-debate
```

## Usage

```
agent-debate [-h] [-f FILE] [-r ROUNDS] [-m MODEL] [-o OUTPUT]
             [--agents AGENT [AGENT ...]] [--api-key API_KEY] [-v]
             [problem]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-f, --file` | Read problem from file | - |
| `-r, --rounds` | Number of debate rounds | 2 |
| `-m, --model` | Claude model to use | claude-sonnet-4-20250514 |
| `-o, --output` | Save report to Markdown file | - |
| `--agents` | Which agents to include | all 5 |
| `--api-key` | Anthropic API key (or use env var) | - |
| `-v, --verbose` | Show token usage | false |

### Examples

```bash
# Security-focused review with 3 rounds
agent-debate -r 3 --agents security architecture moderator -f auth.py

# Quick performance check
agent-debate --agents performance "SELECT * FROM orders WHERE status='pending'"

# Full review, save report
agent-debate -o report.md -f src/handler.py -v
```

## Output

The CLI displays a rich terminal UI with color-coded panels for each agent:

- **Red** - Security
- **Yellow** - Performance
- **Green** - UX
- **Blue** - Architecture
- **Magenta** - Moderator

With `-o report.md`, a structured Markdown report is generated containing:
- Independent analyses with key findings
- Cross-examination highlights
- Rebuttals and position changes
- Final consensus with actionable recommendations
- Dissenting opinions (if any)

## Configuration

Create a `DebateConfig` to customize behavior programmatically:

```python
from agent_debate.config import DebateConfig

config = DebateConfig(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    debate_rounds=3,
    temperature=0.7,
)
```

## Project Structure

```
agent-debate/
├── pyproject.toml
├── src/agent_debate/
│   ├── __init__.py
│   ├── __main__.py        # Entry point
│   ├── cli.py             # CLI interface (Rich)
│   ├── config.py          # Configuration models
│   ├── agent.py           # Agent definitions & prompts
│   ├── llm.py             # Claude API wrapper
│   ├── message.py         # Data models
│   ├── orchestrator.py    # Debate flow orchestration
│   └── reporter.py        # Markdown report generator
└── tests/
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with verbose output
pytest -v
```

## License

MIT
