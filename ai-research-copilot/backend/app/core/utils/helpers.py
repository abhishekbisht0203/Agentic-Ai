"""
Common utility functions for the AI Research Copilot backend.

Provides utilities for UUID generation, secure token generation,
string hashing, datetime handling, file operations, and async utilities.
"""

import asyncio
import hashlib
import logging
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4.

    Returns:
        A new UUID4 instance.
    """
    return uuid.uuid4()


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Uses the secrets module for cryptographically strong random number
    generation suitable for managing tokens, passwords, and authentication.

    Args:
        length: Desired length of the token in characters. Must be positive.

    Returns:
        A random string of the specified length containing alphanumeric characters.

    Raises:
        ValueError: If length is not a positive integer.
    """
    if length <= 0:
        raise ValueError(f"Token length must be positive, got {length}")

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm.

    Args:
        text: The string to hash.
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512).
                  Defaults to sha256.

    Returns:
        Hexadecimal string representation of the hash.

    Raises:
        ValueError: If the specified algorithm is not available.
    """
    try:
        hasher = hashlib.new(algorithm)
        hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()
    except ValueError:
        available = sorted(hashlib.algorithms_guaranteed)
        raise ValueError(
            f"Algorithm '{algorithm}' not available. "
            f"Available algorithms: {', '.join(available)}"
        )


def utc_now() -> datetime:
    """Get the current UTC datetime with timezone information.

    Returns:
        The current datetime in UTC with timezone info attached.
    """
    return datetime.now(timezone.utc)


def format_file_size(size_bytes: int) -> str:
    """Format a file size in bytes to a human-readable string.

    Converts byte values to the most appropriate unit (B, KB, MB, GB, TB, PB).

    Args:
        size_bytes: File size in bytes. Must be non-negative.

    Returns:
        Human-readable file size string (e.g., "1.5 MB", "256 KB").

    Raises:
        ValueError: If size_bytes is negative.
    """
    if size_bytes < 0:
        raise ValueError(f"File size must be non-negative, got {size_bytes}")

    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[unit_index]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing or replacing unsafe characters.

    Replaces characters that are not safe for use in filenames across
    different operating systems while preserving the file extension.

    Args:
        filename: Original filename to sanitize.

    Returns:
        Sanitized filename safe for use on most file systems.
    """
    if not filename:
        return "unnamed"

    name_parts = filename.rsplit(".", 1)
    if len(name_parts) == 2:
        name, ext = name_parts
        ext = "." + ext
    else:
        name = filename
        ext = ""

    safe_chars = set(
        string.ascii_letters + string.digits + "._- "
    )
    sanitized = "".join(c if c in safe_chars else "_" for c in name)

    sanitized = "_".join(filter(None, sanitized.split("_")))

    sanitized = sanitized.strip("_. ")

    if not sanitized:
        sanitized = "unnamed"

    max_name_length = 255 - len(ext)
    if len(sanitized) > max_name_length:
        sanitized = sanitized[:max_name_length]

    return sanitized + ext


def chunk_list(lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Divides the input list into smaller sublists, each containing at most
    chunk_size elements. The last chunk may contain fewer elements if the
    list is not evenly divisible.

    Args:
        lst: The list to split into chunks.
        chunk_size: Maximum size of each chunk. Must be positive.

    Returns:
        A list of lists, where each inner list is a chunk.

    Raises:
        ValueError: If chunk_size is not a positive integer.
    """
    if chunk_size <= 0:
        raise ValueError(f"Chunk size must be positive, got {chunk_size}")

    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_with_timeout(
    coro: Any,
    timeout: float,
    default: Any = None,
) -> Any:
    """Run a coroutine with a timeout.

    Executes the given coroutine and raises an asyncio.TimeoutError if it
    does not complete within the specified timeout period.

    Args:
        coro: The coroutine to execute.
        timeout: Maximum time to wait in seconds. Must be positive.
        default: Value to return if the coroutine times out. If None,
                TimeoutError is raised on timeout.

    Returns:
        The result of the coroutine, or the default value if timeout occurs
        and default is not None.

    Raises:
        asyncio.TimeoutError: If the coroutine times out and default is None.
        TypeError: If coro is not a coroutine or awaitable.

    Example:
        >>> result = await run_with_timeout(slow_operation(), timeout=5.0, default="fallback")
    """
    if timeout <= 0:
        raise ValueError(f"Timeout must be positive, got {timeout}")

    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        if default is None:
            logger.error("Operation timed out after %.2f seconds", timeout)
            raise
        logger.warning(
            "Operation timed out after %.2f seconds, using default", timeout
        )
        return default
