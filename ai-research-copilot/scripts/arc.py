#!/usr/bin/env python3
"""
ARC CLI - AI Research Copilot Terminal Agent.

Usage:
    arc "implement a login page"
    arc --plan "design the database schema"
    arc --repl             (interactive mode)
    arc --serve            (start MCP server for VS Code integration)

Environment:
    OPENCODE_API_KEY   (required for LLM access)
    ARC_API_URL        (optional, default: http://localhost:8000/api/v1)
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Add backend to path for direct imports
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# Imports (backed by backend code when available, standalone fallback otherwise)
# ---------------------------------------------------------------------------

_HAS_BACKEND = False
try:
    from app.agents.cli_agent.cli_agent import CLIAgent
    from app.llms.factory import LLMFactory
    from app.mcp.registry.tool_registry import ToolRegistry
    from app.mcp.tools.builtin_tools import register_built_in_tools
    from app.mcp.tools.coding_tools import register_coding_tools

    _HAS_BACKEND = True
except ImportError:
    CLIAgent = None
    LLMFactory = None


# ---------------------------------------------------------------------------
# Terminal UI helpers
# ---------------------------------------------------------------------------

def _style(text: str, color: str = "") -> str:
    colors = {
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    if not sys.stdout.isatty():
        return text
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def _print_banner():
    banner = r"""
    ╔═══════════════════════════════════╗
    ║   ARC - AI Research Copilot      ║
    ║   Terminal Agent Mode            ║
    ╚═══════════════════════════════════╝
    """
    print(_style(banner, "cyan"))
    print(_style("  Type '/help' for commands, '/exit' to quit\n", "dim"))


def _print_help():
    help_text = """
  Commands:
    /help          Show this help message
    /exit, /quit   Exit the CLI
    /plan <task>   Plan without executing
    /status        Show agent status
    /clear         Clear conversation history

  Examples:
    arc "find all .py files with TODO comments"
    arc --plan "design a REST API for user management"
    arc --repl

  Environment:
    OPENCODE_API_KEY   Required for LLM access
    ARC_API_URL        API endpoint (default: http://localhost:8000)
    ARC_WORKSPACE      Workspace directory (default: current directory)
    """
    print(_style(help_text, "dim"))


# ---------------------------------------------------------------------------
# Core CLI Logic
# ---------------------------------------------------------------------------


def _get_llm_provider():
    """Try to get an LLM provider, falling back through options."""
    if not LLMFactory:
        return None

    factory = LLMFactory(default_provider="opencode")
    for name in ["opencode", "openai", "anthropic"]:
        try:
            provider = factory.get_provider(name)
            return provider
        except Exception:
            continue
    return None


def _create_agent() -> Any:
    """Create a CLI agent instance."""
    if not _HAS_BACKEND:
        print(_style("Error: Backend modules not available.", "red"))
        print("Run: pip install -e backend/")
        sys.exit(1)

    provider = _get_llm_provider()
    if provider is None:
        print(_style(
            "Error: No LLM provider available.\n"
            "Set OPENCODE_API_KEY in your .env file.\n"
            "Get a free key at https://opencode.ai/zen",
            "red",
        ))
        sys.exit(1)

    return CLIAgent(provider)


async def _execute_single(agent: CLIAgent, task: str, plan_only: bool = False) -> None:
    """Execute a single task and print the result."""
    print(_style(f"\n{'─' * 60}", "dim"))
    print(_style(f"  Task: {task[:100]}", "bold"))
    print(_style(f"{'─' * 60}\n", "dim"))

    try:
        result = await agent.execute(
            {"message": task, "task_type": "plan_only" if plan_only else "execute"},
        )

        if plan_only:
            title = result.get("plan_title", task[:60])
            print(_style(f"  Plan: {title}", "bold"))
            for step in result.get("steps", []):
                print(f"    {step.get('step', '?')}. {step.get('action', step.get('title', ''))}")
            print()
        else:
            thought = result.get("thought", "")
            if thought:
                print(_style(f"  {thought}", "dim"))
                print()

            tool_calls = result.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name", "?")
                args = tc.get("arguments", {})
                print(_style(f"  🔧 {name}", "yellow"))
                for k, v in list(args.items())[:3]:
                    print(f"    {k}: {str(v)[:80]}")
                print()

            response = result.get("response", "")
            if response:
                print(_style(response, "green"))
            print()

        if result.get("done"):
            print(_style(f"{'─' * 60}", "dim"))

    except Exception as exc:
        print(_style(f"  Error: {exc}", "red"))


async def _repl(agent: CLIAgent) -> None:
    """Run interactive REPL mode."""
    _print_banner()

    while True:
        try:
            user_input = input(_style("arc> ", "cyan")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input[1:].lower().split()
            if not cmd:
                continue

            if cmd[0] in ("exit", "quit"):
                print(_style("Goodbye!", "cyan"))
                break

            if cmd[0] == "help":
                _print_help()
                continue

            if cmd[0] == "clear":
                agent._conversation_history = []
                print(_style("History cleared.", "dim"))
                continue

            if cmd[0] == "plan" and len(cmd) > 1:
                task = " ".join(cmd[1:])
                await _execute_single(agent, task, plan_only=True)
                continue

            if cmd[0] == "status":
                info = agent.to_dict()
                print(f"  Agent type: {info.get('agent_type', '?')}")
                print(f"  History length: {info.get('cli_history_length', 0)}")
                continue

            print(_style(f"Unknown command: /{cmd[0]}", "red"))
            continue

        start = time.monotonic()
        try:
            result = await agent.chat(user_input)
            elapsed = time.monotonic() - start
            response = result.get("response", "")
            if response:
                print()
                print(_style(response, "green"))
                print()
            print(_style(f"  [{elapsed:.1f}s]", "dim"))
        except Exception as exc:
            print(_style(f"  Error: {exc}", "red"))


# ---------------------------------------------------------------------------
# MCP Server mode (for VS Code / IDE integration)
# ---------------------------------------------------------------------------


def _start_mcp_server(host: str = "0.0.0.0", port: int = 8100) -> None:
    """Start the MCP server (imported from backend)."""
    try:
        import uvicorn
        from app.mcp.server.main import create_mcp_app

        app = create_mcp_app()
        print(_style(f"Starting MCP server on {host}:{port}...", "green"))
        uvicorn.run(app, host=host, port=port, log_level="info")
    except ImportError as exc:
        print(_style(f"Error: Cannot start MCP server - {exc}", "red"))
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="ARC CLI - AI Research Copilot Terminal Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  arc "find all Python files with TODO comments"
  arc --plan "design authentication system"
  arc --repl
  arc --serve
        """,
    )
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--plan", action="store_true", help="Plan only, don't execute")
    parser.add_argument("--repl", action="store_true", help="Start interactive REPL mode")
    parser.add_argument("--serve", action="store_true", help="Start MCP server for IDE integration")
    parser.add_argument("--host", default="0.0.0.0", help="MCP server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8100, help="MCP server port (default: 8100)")

    args = parser.parse_args()

    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        print()
        print("Run 'arc --repl' for interactive mode or 'arc <task>' for single commands.")
        return

    # MCP server mode (for VS Code)
    if args.serve:
        _start_mcp_server(host=args.host, port=args.port)
        return

    # REPL mode
    if args.repl:
        agent = _create_agent()
        asyncio.run(_repl(agent))
        return

    # Single task mode
    if args.task:
        agent = _create_agent()
        asyncio.run(_execute_single(agent, args.task, plan_only=args.plan))
        return


if __name__ == "__main__":
    main()
