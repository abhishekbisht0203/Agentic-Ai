"""
MCP Built-in Tools.

Collection of built-in tools that are registered into the ToolRegistry
on application startup. Includes:

- **calculator** – evaluate mathematical expressions safely.
- **web_search** – stub web search returning simulated results.
- **weather** – stub weather lookup returning mock data.
- **read_file / write_file** – local filesystem read/write.
- **python_executor** – restricted Python code execution via ``exec``.
"""

import ast
import io
import logging
import math
import operator
import contextlib
from pathlib import Path
from typing import Any

from app.mcp.registry.tool_registry import MCPTool, ToolRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safe math evaluator (no imports, no dunder access)
# ---------------------------------------------------------------------------

_SAFE_OPERATORS: dict[Any, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}


def _safe_eval(node: ast.AST) -> Any:
    """Recursively evaluate an AST node using only safe operators.

    Args:
        node: The AST node to evaluate.

    Returns:
        The numeric result of the expression.

    Raises:
        ValueError: If the expression contains unsupported constructs.
    """
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _SAFE_OPERATORS[op_type](_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCTIONS:
            func = _SAFE_FUNCTIONS[node.func.id]
            if callable(func):
                args = [_safe_eval(arg) for arg in node.args]
                return func(*args)
            return func  # constant like pi / e
        raise ValueError(f"Unsupported function call")
    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCTIONS:
            val = _SAFE_FUNCTIONS[node.id]
            if not callable(val):
                return val
        raise ValueError(f"Unsupported name: {node.id}")
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


# ---------------------------------------------------------------------------
# Tool handler functions
# ---------------------------------------------------------------------------


async def calculator_handler(expression: str = "", **kwargs: Any) -> str:
    """Evaluate a mathematical expression safely.

    Supports basic arithmetic (+, -, *, /, //, %, **), common math
    functions (sqrt, sin, cos, tan, log, abs, round, min, max, ceil,
    floor), and the constants ``pi`` and ``e``.

    Args:
        expression: The mathematical expression string to evaluate.

    Returns:
        The result as a string.

    Raises:
        ValueError: If the expression is invalid or contains disallowed constructs.
    """
    if not expression or not expression.strip():
        raise ValueError("Expression cannot be empty")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        return str(result)
    except (SyntaxError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid expression '{expression}': {exc}") from exc


async def web_search_handler(query: str = "", num_results: int = 5, **kwargs: Any) -> dict[str, Any]:
    """Stub web search returning simulated results.

    In production this would call a real search API (e.g. SerpAPI,
    Brave Search). For now it returns structured placeholder results.

    Args:
        query: The search query string.
        num_results: Number of results to return (max 10).

    Returns:
        A dictionary with a ``results`` list.
    """
    num_results = min(max(num_results, 1), 10)
    results = []
    for i in range(1, num_results + 1):
        results.append(
            {
                "title": f"Result {i} for '{query}'",
                "url": f"https://example.com/search/{i}",
                "snippet": f"This is a simulated search result snippet for query '{query}'. "
                "In production, this would contain real web content.",
                "position": i,
            }
        )
    return {"query": query, "results": results, "total": len(results)}


async def weather_handler(
    location: str = "", units: str = "celsius", **kwargs: Any
) -> dict[str, Any]:
    """Stub weather lookup returning mock data.

    In production this would call a real weather API (e.g. OpenWeatherMap).

    Args:
        location: City or location name.
        units: Temperature units – ``celsius`` or ``fahrenheit``.

    Returns:
        A dictionary with simulated weather information.
    """
    temp_c = 22.5
    if units == "fahrenheit":
        temp_display = f"{temp_c * 9 / 5 + 32:.1f}°F"
    else:
        temp_display = f"{temp_c:.1f}°C"

    return {
        "location": location or "Unknown",
        "temperature": temp_display,
        "condition": "Partly Cloudy",
        "humidity": 65,
        "wind_speed_kmh": 12.3,
        "units": units,
        "forecast": [
            {"day": "Today", "high": "25°C", "low": "18°C", "condition": "Partly Cloudy"},
            {"day": "Tomorrow", "high": "23°C", "low": "17°C", "condition": "Overcast"},
            {"day": "Day After", "high": "27°C", "low": "19°C", "condition": "Sunny"},
        ],
    }


async def read_file_handler(file_path: str = "", **kwargs: Any) -> dict[str, Any]:
    """Read the contents of a local file.

    The file must exist and be readable. Binary files are returned
    as a base64-encoded string.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        A dictionary with ``content``, ``size``, and ``encoding`` fields.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file is not readable.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
        return {
            "content": content,
            "size": len(content),
            "encoding": "utf-8",
            "path": str(path.resolve()),
        }
    except UnicodeDecodeError:
        import base64

        raw = path.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        return {
            "content": encoded,
            "size": len(raw),
            "encoding": "base64",
            "path": str(path.resolve()),
        }


async def write_file_handler(
    file_path: str = "", content: str = "", **kwargs: Any
) -> dict[str, Any]:
    """Write content to a local file, creating parent directories if needed.

    If the file already exists it will be overwritten.

    Args:
        file_path: Absolute or relative path to the target file.
        content: The text content to write.

    Returns:
        A dictionary with ``bytes_written`` and ``path``.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Written %d bytes to %s", len(content), file_path)
    return {
        "bytes_written": len(content.encode("utf-8")),
        "path": str(path.resolve()),
    }


async def python_executor_handler(code: str = "", **kwargs: Any) -> dict[str, Any]:
    """Execute a Python code snippet in a restricted environment.

    stdout and stderr are captured. The execution has access to a
    limited set of builtins – no file I/O, no imports, no network.

    Args:
        code: Python source code to execute.

    Returns:
        A dictionary with ``stdout``, ``stderr``, and ``result`` fields.
    """
    if not code or not code.strip():
        raise ValueError("Code cannot be empty")

    safe_builtins = {
        "abs": abs,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "frozenset": frozenset,
        "int": int,
        "isinstance": isinstance,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "print": print,
        "range": range,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
        "True": True,
        "False": False,
        "None": None,
    }

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result_value = None

    try:
        compiled = compile(code, "<mcp_executor>", "exec")
        exec_globals: dict[str, Any] = {"__builtins__": safe_builtins}
        exec_locals: dict[str, Any] = {}

        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(
            stderr_capture
        ):
            exec(compiled, exec_globals, exec_locals)  # noqa: S102

        # If the last statement is an expression, capture its value
        try:
            tree = ast.parse(code)
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                last_expr = ast.dump(tree.body[-1].value)
                for key, val in exec_locals.items():
                    if key.startswith("_"):
                        continue
                    result_value = val
                    break
        except SyntaxError:
            pass

        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "result": str(result_value) if result_value is not None else None,
        }

    except Exception as exc:
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue() or str(exc),
            "result": None,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_built_in_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools into the given ToolRegistry.

    Called once during application startup to populate the registry
    with the standard tool set.

    Args:
        registry: The ToolRegistry instance to populate.
    """
    tools = [
        MCPTool(
            name="calculator",
            description=(
                "Evaluate a mathematical expression. Supports arithmetic "
                "operators, common math functions (sqrt, sin, cos, tan, log, "
                "abs, round, min, max, ceil, floor), and constants (pi, e)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
            handler=calculator_handler,
            category="calculation",
            requires_auth=False,
        ),
        MCPTool(
            name="web_search",
            description="Search the web for information on a given query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-10, default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            handler=web_search_handler,
            category="search",
            requires_auth=False,
        ),
        MCPTool(
            name="weather",
            description="Get current weather information for a location.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location name.",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units (default: celsius).",
                        "default": "celsius",
                    },
                },
                "required": ["location"],
            },
            handler=weather_handler,
            category="data",
            requires_auth=False,
        ),
        MCPTool(
            name="read_file",
            description="Read the contents of a local file.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read.",
                    }
                },
                "required": ["file_path"],
            },
            handler=read_file_handler,
            category="filesystem",
            requires_auth=True,
        ),
        MCPTool(
            name="write_file",
            description="Write content to a local file, creating directories as needed.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write.",
                    },
                },
                "required": ["file_path", "content"],
            },
            handler=write_file_handler,
            category="filesystem",
            requires_auth=True,
        ),
        MCPTool(
            name="python_executor",
            description="Execute a Python code snippet and return stdout/stderr.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to execute.",
                    }
                },
                "required": ["code"],
            },
            handler=python_executor_handler,
            category="execution",
            requires_auth=True,
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(
        "Registered %d built-in MCP tools: %s",
        len(tools),
        ", ".join(t.name for t in tools),
    )
