"""
JSON response parser for extracting structured data from LLM outputs.

Handles common patterns where LLMs embed JSON inside markdown fences
or return raw JSON payloads.
"""

import json
import logging
import re
from typing import Any

from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)

# Matches ```json ... ``` or ``` ... ``` blocks
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)


class JSONParser:
    """
    Parse JSON content from LLM responses.

    Tries, in order:
    1. Direct ``json.loads`` of the raw text.
    2. Extraction from a markdown fenced code block.
    3. Extraction of the first ``{...}`` or ``[...]`` substring.
    """

    @staticmethod
    def parse(text: str, *, strict: bool = False) -> Any:
        """
        Extract and deserialise JSON from *text*.

        Args:
            text: Raw LLM output potentially containing JSON.
            strict: When True, raise ``LLMError`` if no valid JSON is found.
                    When False, return ``None`` on failure.

        Returns:
            Parsed JSON object, or ``None`` when parsing fails and *strict* is False.

        Raises:
            LLMError: When *strict* is True and parsing fails.
        """
        if not text or not text.strip():
            return None

        # 1. Try direct parse
        result = JSONParser._try_load(text)
        if result is not None:
            return result

        # 2. Try fenced code block
        match = _JSON_FENCE_RE.search(text)
        if match:
            result = JSONParser._try_load(match.group(1))
            if result is not None:
                return result

        # 3. Try to find first {…} or […] block
        result = JSONParser._extract_outer_json(text)
        if result is not None:
            return result

        if strict:
            raise LLMError(
                message="Failed to extract valid JSON from LLM response",
                details={"preview": text[:500]},
            )
        return None

    @staticmethod
    def parse_list(text: str, *, strict: bool = False) -> list[Any]:
        """
        Parse a JSON array from LLM output.

        Falls back to an empty list when parsing fails and *strict* is False.
        """
        result = JSONParser.parse(text, strict=False)
        if isinstance(result, list):
            return result
        if strict:
            raise LLMError(
                message="Expected a JSON array but did not find one",
                details={"preview": text[:500]},
            )
        return []

    @staticmethod
    def parse_dict(text: str, *, strict: bool = False) -> dict[str, Any]:
        """
        Parse a JSON object from LLM output.

        Falls back to an empty dict when parsing fails and *strict* is False.
        """
        result = JSONParser.parse(text, strict=False)
        if isinstance(result, dict):
            return result
        if strict:
            raise LLMError(
                message="Expected a JSON object but did not find one",
                details={"preview": text[:500]},
            )
        return {}

    @staticmethod
    def validate_schema(data: Any, required_keys: list[str]) -> bool:
        """
        Check that *data* is a dict containing all *required_keys*.

        Returns True if valid, False otherwise.
        """
        if not isinstance(data, dict):
            return False
        return all(key in data for key in required_keys)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _try_load(text: str) -> Any:
        """Attempt ``json.loads``; return None on failure."""
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _extract_outer_json(text: str) -> Any:
        """
        Find the outermost ``{…}`` or ``[…]`` bracket pair and parse it.

        Handles nested structures by tracking bracket depth.
        """
        for open_char, close_char in [("{", "}"), ("[", "]")]:
            start = text.find(open_char)
            if start == -1:
                continue
            depth = 0
            in_string = False
            escape = False
            for idx in range(start, len(text)):
                ch = text[idx]
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == open_char:
                    depth += 1
                elif ch == close_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : idx + 1]
                        result = JSONParser._try_load(candidate)
                        if result is not None:
                            return result
                        break
        return None
