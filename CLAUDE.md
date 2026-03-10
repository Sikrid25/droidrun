# DroidRun

## Overview

DroidRun is an open-source Python framework (MIT) for controlling Android and iOS devices through LLM agents. It enables mobile automation via natural language commands — an AI agent observes the screen, plans steps, and executes UI interactions like a human would.

- **Version:** 0.5.1.dev1
- **Python:** 3.11 – 3.13
- **Docs:** https://docs.droidrun.ai
- **Repo:** https://github.com/droidrun/droidrun

## Architecture

### Multi-Agent System

```
DroidAgent (Orchestrator)
├── Reasoning Mode (reasoning=True)
│   ├── ManagerAgent  → Plans and decomposes goals into subgoals
│   ├── ExecutorAgent  → Executes each subgoal via atomic actions
│   └── Loop until task_complete()
│
├── Direct Mode (reasoning=False)
│   ├── FastAgent (XML tool-calling, default)
│   └── CodeActAgent (generates + exec() Python code)
│
├── Auxiliary Agents
│   ├── ScripterAgent          → Off-device computation
│   ├── StructuredOutputAgent  → Typed data extraction
│   └── External Agents        → mai_ui, autoglm
│
└── Support Systems
    ├── ToolRegistry    → Central tool discovery & execution
    ├── ActionContext    → ctx.driver, ctx.ui, ctx.shared_state
    └── Trajectory      → Execution history tracking
```

### Device Driver Layer

| Driver | Transport | Purpose |
|--------|-----------|---------|
| `AndroidDriver` | ADB + Portal APK | Physical/emulator Android devices |
| `IOSDriver` | HTTP API | iOS devices |
| `CloudDriver` | mobilerun-sdk | Cloud-hosted devices |
| `RecordingDriver` | File playback | Testing/replay |
| `StealthDriver` | Wrapper | Anti-detection mode |

### UI State Pipeline

```
DeviceDriver.get_ui_tree() → TreeFilter (concise/detailed) → TreeFormatter (indexed) → UIState snapshot
```

Each UI element has: `index`, `text`, `className`, `type`, `bounds`, `clickable`, etc.

## Project Structure

```
droidrun/
├── agent/                  # AI agent system
│   ├── droid/              # DroidAgent orchestrator
│   ├── codeact/            # CodeActAgent (direct Python execution)
│   ├── executor/           # ExecutorAgent (action execution)
│   ├── manager/            # ManagerAgent (planning)
│   ├── scripter/           # ScripterAgent (off-device compute)
│   ├── oneflows/           # StructuredOutputAgent
│   ├── external/           # External agents (mai_ui, autoglm)
│   ├── common/             # Shared agent utilities
│   ├── utils/              # LLM loading, prompts, actions, tracing
│   │   ├── llm_picker.py   # load_llm() — multi-provider LLM factory
│   │   └── actions.py      # Atomic action implementations
│   ├── tool_registry.py    # Central tool registry
│   └── action_context.py   # Context passed to every action
│
├── tools/                  # Device interaction layer
│   ├── driver/             # Device drivers (android, ios, cloud, recording, stealth)
│   ├── ui/                 # UI state (StateProvider, UIState)
│   ├── filters/            # UI tree filtering
│   ├── formatters/         # UI tree formatting for LLM prompts
│   ├── android/            # Android-specific (Portal client)
│   ├── ios/                # iOS-specific tools
│   └── helpers/            # Geometry, coordinate utilities
│
├── cli/                    # Click CLI
│   ├── main.py             # Entry point: droidrun CLI commands
│   ├── doctor.py           # System diagnostics
│   ├── event_handler.py    # Event streaming & display
│   └── tui/                # Textual terminal UI
│
├── config/                 # Configuration templates
│   ├── prompts/            # Jinja2 prompt templates (codeact, manager, executor, scripter)
│   └── app_cards/          # App-specific instruction cards
│
├── config_manager/         # YAML config loading (dataclasses, loader, migrations)
├── credential_manager/     # Secure credential storage
├── macro/                  # Macro recording/playback
├── mcp/                    # Model Context Protocol integration
├── telemetry/              # Arize Phoenix / Langfuse observability
├── app_cards/              # App-specific instruction card system
├── portal.py               # Android Portal APK management
├── config_example.yaml     # Full config reference
└── __init__.py             # Package exports (DroidAgent, load_llm, etc.)
```

## Key Concepts

### Atomic Actions
Low-level device operations available to agents:
- `click(index)`, `long_press(index)` — tap UI elements
- `type(text)` — input text
- `swipe(x1,y1,x2,y2)` — gestures
- `system_button(name)` — back, home, enter
- `open_app(app_id)` — launch applications
- `get_state()` — fetch UI snapshot
- `take_screenshot()` — capture screen
- `remember(key, value)` — persist data across turns
- `complete()` — mark goal as done

### LLM Profiles
Each agent role has its own LLM config in `config.yaml` under `llm_profiles`:
- `manager`, `executor`, `fast_agent`, `scripter`, `text_manipulator`, `app_opener`, `structured_output`

### Supported LLM Providers
OpenAI, Anthropic (optional), Google Gemini, Ollama, DeepSeek (optional), OpenRouter

### Configuration
YAML-based config at `~/.droidrun/config.yaml` (auto-generated from `config_example.yaml`). Covers: agent settings, LLM profiles, device, tracing, tools, credentials, MCP, safe execution.

## Development

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Code Quality

```bash
black .                    # Format (line-length from pyproject.toml)
ruff check droidrun/       # Lint
mypy droidrun/             # Type check
bandit -r droidrun/        # Security audit
safety scan                # Dependency vulnerabilities
```

### Style Rules
- **Formatter:** Black (25.9.0)
- **Linter:** Ruff — rules: E, W, F, I, B (ignores E501)
- **Line length:** 100 (ruff), Black default (88)
- **Target:** Python 3.13
- **Type hints** required on all functions
- **Docstrings** on public classes and functions
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Language:** English for all code, comments, docs, and commits

### Running

```bash
# CLI
droidrun "open Chrome and search for cats"
droidrun --reasoning "book a flight on Skyscanner"
droidrun --vision "describe what's on screen"
droidrun --provider Anthropic --model claude-3-5-sonnet "goal"
droidrun tui                  # Interactive terminal UI
droidrun doctor               # System diagnostics

# Python SDK
from droidrun import DroidAgent, load_llm
llm = load_llm("GoogleGenAI", "models/gemini-2.5-pro")
agent = DroidAgent(device_serial="emulator-5554", llm=llm, reasoning=True)
result = await agent.run("Open Settings and enable Dark Mode")
```

## Dependencies (Core)

| Package | Purpose |
|---------|---------|
| llama-index 0.14.4 | LLM orchestration framework |
| llama-index-workflows 2.8.3 | Async event-driven agent workflows |
| pydantic ≥2.11.10 | Data validation & config models |
| async_adbutils | ADB communication (Android) |
| httpx ≥0.27.0 | HTTP client (iOS driver, APIs) |
| rich ≥14.1.0 | Console UI / pretty printing |
| textual ≥6.11.0 | Terminal UI framework |
| click | CLI framework |
| mcp ≥1.26.0 | Model Context Protocol |
| mobilerun-sdk | Cloud device management |
| arize-phoenix ≥12.3.0 | Observability / tracing |

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `black.yml` | Push/PR | Code formatting check |
| `claude.yml` | PR | Claude Code review |
| `claude-code-review.yml` | PR | Automated code review |
| `docker.yml` | Release | Docker image build & publish |
| `publish.yml` | Release | PyPI package publish |
| `bounty.yml` | Labels | Bounty project automation |

Build backend: **Hatchling**
