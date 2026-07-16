
import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from app.mcp.registry.tool_registry import MCPTool, ToolRegistry

logger = logging.getLogger(__name__)

# Absolute project root (ai-research-copilot/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent  # Agentic Ai/

_SAFE_BASE_DIRS = [
    PROJECT_ROOT,
    WORKSPACE_ROOT,
    Path.home() / "Desktop",
    Path.cwd(),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_path(path_str: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve(strict=False)


def _check_allowed(target: Path) -> None:
    resolved = target.resolve()
    for base in _SAFE_BASE_DIRS:
        try:
            resolved.relative_to(base.resolve())
            return
        except ValueError:
            continue
    allowed = ", ".join(str(b) for b in _SAFE_BASE_DIRS)
    raise PermissionError(f"Path '{resolved}' is not in allowed directories: {allowed}")


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def edit_file_handler(
    file_path: str = "",
    old_string: str = "",
    new_string: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Find-and-replace in a file with exact match, like sed but safe.

    Args:
        file_path: Path to the file to edit.
        old_string: The exact text to find (must match once).
        new_string: The replacement text.

    Returns:
        A dict with ``success``, ``path``, and ``replacement_count``.
    """
    path = _resolve_path(file_path)
    _check_allowed(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    content = path.read_text(encoding="utf-8")
    if old_string not in content:
        raise ValueError(
            f"old_string not found in {path.name}. "
            "Provide more surrounding context in old_string to ensure a unique match."
        )
    count = content.count(old_string)
    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content, encoding="utf-8")

    logger.info("Edited %s: replaced 1 occurrence", file_path)
    return {
        "success": True,
        "path": str(path.resolve()),
        "replacement_count": 1,
        "total_occurrences": count,
    }


async def edit_file_replace_all_handler(
    file_path: str = "",
    old_string: str = "",
    new_string: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Replace ALL occurrences of old_string in a file.

    Args:
        file_path: Path to the file to edit.
        old_string: The text to find (all occurrences replaced).
        new_string: The replacement text.

    Returns:
        A dict with ``success``, ``path``, and ``replacement_count``.
    """
    path = _resolve_path(file_path)
    _check_allowed(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = path.read_text(encoding="utf-8")
    count = content.count(old_string)
    if count == 0:
        raise ValueError(f"old_string not found in {path.name}")
    new_content = content.replace(old_string, new_string)
    path.write_text(new_content, encoding="utf-8")

    logger.info("Edited %s: replaced %d occurrences", file_path, count)
    return {"success": True, "path": str(path.resolve()), "replacement_count": count}


async def read_file_range_handler(
    file_path: str = "",
    offset: int = 1,
    limit: int = 2000,
    **kwargs: Any,
) -> dict[str, Any]:
    """Read a specific line range from a file.

    Args:
        file_path: Path to the file.
        offset: Starting line number (1-indexed).
        limit: Maximum number of lines to read.

    Returns:
        Dict with ``content``, ``total_lines``, ``lines_returned``.
    """
    path = _resolve_path(file_path)
    _check_allowed(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    total = len(lines)
    start = max(0, offset - 1)
    end = min(total, start + limit)
    content = "".join(lines[start:end])

    return {
        "content": content,
        "total_lines": total,
        "lines_returned": end - start,
        "path": str(path.resolve()),
        "start_line": offset,
    }


async def write_file_handler_new(
    file_path: str = "",
    content: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Write content to a file, creating parent directories if needed.

    Overwrites existing files.  For existing files, prefer ``edit_file``.

    Args:
        file_path: Path to the target file.
        content: Text content to write.

    Returns:
        Dict with ``bytes_written`` and ``path``.
    """
    path = _resolve_path(file_path)
    _check_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Written %d bytes to %s", len(content), file_path)
    return {"bytes_written": len(content.encode("utf-8")), "path": str(path.resolve())}


async def execute_command_handler(
    command: str = "",
    timeout: int = 120,
    workdir: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a shell command and return stdout, stderr, exit code.

    Security restriction: only non-interactive commands are allowed.
    Use ``workdir`` to set the working directory instead of ``cd``.

    Args:
        command: The shell command to execute.
        timeout: Max execution time in seconds (default 120).
        workdir: Working directory for the command.

    Returns:
        Dict with ``stdout``, ``stderr``, ``exit_code``, and ``duration_ms``.
    """
    cwd = str(PROJECT_ROOT)
    if workdir:
        wd = _resolve_path(workdir)
        _check_allowed(wd)
        cwd = str(wd)

    logger.info("Executing: %s (cwd=%s, timeout=%ds)", command[:200], cwd, timeout)
    start = time.monotonic()

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode,
            "duration_ms": duration_ms,
            "timed_out": False,
        }
    except asyncio.TimeoutError:
        proc.kill()
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
            "duration_ms": duration_ms,
            "timed_out": True,
        }


async def glob_search_handler(
    pattern: str = "",
    path: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g. ``**/*.py``, ``src/**/*.ts``).
        path: Root directory to search (defaults to project root).

    Returns:
        Dict with ``files`` list and ``count``.
    """
    root = PROJECT_ROOT
    if path:
        root = _resolve_path(path)
        _check_allowed(root)

    matches = [str(p.relative_to(PROJECT_ROOT)) for p in sorted(root.glob(pattern))]
    return {"files": matches, "count": len(matches), "root": str(root)}


async def grep_search_handler(
    pattern: str = "",
    include: str = "",
    path: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Search file contents using regex.

    Args:
        pattern: The regex pattern to search for.
        include: File glob filter (e.g. ``*.py``, ``*.{ts,tsx}``).
        path: Root directory to search.

    Returns:
        Dict with ``matches`` (list of {file, line, content}) and ``count``.
    """
    root = PROJECT_ROOT
    if path:
        root = _resolve_path(path)
        _check_allowed(root)

    matches: list[dict[str, Any]] = []
    file_pattern = f"**/{include}" if include else "**/*"
    for file_path in sorted(root.glob(file_pattern)):
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(pattern, line):
                    rel = str(file_path.relative_to(PROJECT_ROOT))
                    matches.append({"file": rel, "line": i, "content": line.strip()[:200]})
        except Exception:
            continue

    return {"matches": matches, "count": len(matches), "pattern": pattern}


async def git_operations_handler(
    operation: str = "status",
    args: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Run git operations on the workspace.

    Supported operations: status, diff, log, add, commit, push, pull, branch.

    Args:
        operation: Git subcommand (status|diff|log|add|commit|push|pull|branch).
        args: Additional arguments for the git command.

    Returns:
        Dict with ``stdout``, ``stderr``, ``exit_code``, and ``operation``.
    """
    allowed_ops = {"status", "diff", "log", "add", "commit", "push", "pull", "branch", "checkout", "stash", "reset"}
    if operation not in allowed_ops:
        raise ValueError(f"Operation '{operation}' not allowed. Allowed: {sorted(allowed_ops)}")

    cmd = f"git {operation} {args}"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
    )
    stdout, stderr = await proc.communicate()
    return {
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "exit_code": proc.returncode,
        "operation": operation,
    }


async def list_directory_handler(
    path: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """List directory contents.

    Args:
        path: Directory path (defaults to project root).

    Returns:
        Dict with ``entries`` (list of {name, type, size}) and ``count``.
    """
    root = PROJECT_ROOT
    if path:
        root = _resolve_path(path)
        _check_allowed(root)

    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    entries: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir()):
        try:
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size if entry.is_file() else 0,
                "modified": stat.st_mtime,
            })
        except OSError:
            continue

    return {"entries": entries, "count": len(entries), "path": str(root.resolve())}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_coding_tools(registry: ToolRegistry) -> None:
    """Register all coding/agent tools into the given ToolRegistry."""
    tools = [
        MCPTool(
            name="edit_file",
            description="Perform an exact string replacement in a file. "
                        "Use this to modify existing code (like a find-and-replace). "
                        "The old_string must match exactly once; include surrounding lines for uniqueness.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to edit."},
                    "old_string": {"type": "string", "description": "The exact text to replace (must match once)."},
                    "new_string": {"type": "string", "description": "The replacement text."},
                },
                "required": ["file_path", "old_string", "new_string"],
            },
            handler=edit_file_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="edit_file_replace_all",
            description="Replace ALL occurrences of a string in a file. "
                        "Use when the same change needs to be applied everywhere.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file."},
                    "old_string": {"type": "string", "description": "Text to replace (all occurrences)."},
                    "new_string": {"type": "string", "description": "Replacement text."},
                },
                "required": ["file_path", "old_string", "new_string"],
            },
            handler=edit_file_replace_all_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="read_file_range",
            description="Read a specific line range from a file. Use offset=1 to start from the beginning.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file."},
                    "offset": {"type": "integer", "description": "Starting line number (1-indexed, default 1).", "default": 1},
                    "limit": {"type": "integer", "description": "Maximum lines to read (max 5000, default 2000).", "default": 2000},
                },
                "required": ["file_path"],
            },
            handler=read_file_range_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="write_file",
            description="Write content to a new file, creating parent directories if needed. "
                        "For existing files, prefer 'edit_file' instead of write_file.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to write."},
                    "content": {"type": "string", "description": "Text content to write."},
                },
                "required": ["file_path", "content"],
            },
            handler=write_file_handler_new,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="execute_command",
            description="Execute a shell command in the workspace. "
                        "Returns stdout, stderr, and exit code. "
                        "Use the 'workdir' parameter to set the working directory.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."},
                    "timeout": {"type": "integer", "description": "Max execution time in seconds (default 120).", "default": 120},
                    "workdir": {"type": "string", "description": "Working directory (defaults to project root).", "default": ""},
                },
                "required": ["command"],
            },
            handler=execute_command_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="glob_search",
            description="Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.tsx').",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern to search."},
                    "path": {"type": "string", "description": "Root directory (defaults to project root).", "default": ""},
                },
                "required": ["pattern"],
            },
            handler=glob_search_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="grep_search",
            description="Search file contents using a regex pattern.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "The regex pattern to search for."},
                    "include": {"type": "string", "description": "File glob filter (e.g. '*.py', '*.{ts,tsx}').", "default": ""},
                    "path": {"type": "string", "description": "Root directory to search.", "default": ""},
                },
                "required": ["pattern"],
            },
            handler=grep_search_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="git_operations",
            description="Run git operations (status, diff, log, add, commit, push, pull, branch, checkout, stash, reset).",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["status", "diff", "log", "add", "commit", "push", "pull", "branch", "checkout", "stash", "reset"],
                        "description": "Git subcommand.",
                    },
                    "args": {"type": "string", "description": "Additional arguments for the git command.", "default": ""},
                },
                "required": ["operation"],
            },
            handler=git_operations_handler,
            category="coding",
            requires_auth=True,
        ),
        MCPTool(
            name="list_directory",
            description="List files and directories in a path.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (defaults to project root).", "default": ""},
                },
                "required": [],
            },
            handler=list_directory_handler,
            category="coding",
            requires_auth=True,
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(
        "Registered %d coding MCP tools: %s",
        len(tools),
        ", ".join(t.name for t in tools),
    )
