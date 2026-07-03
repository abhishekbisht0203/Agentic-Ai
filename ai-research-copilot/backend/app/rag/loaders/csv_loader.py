"""
CSV document loader.

Extracts tabular data from CSV files using pandas and converts rows to text.
"""

import logging
from io import BytesIO

import pandas as pd

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)


class CSVLoader(BaseDocumentLoader):
    """Load and extract text from CSV files."""

    async def load(self, content: bytes, filename: str) -> str:
        """Extract text from a CSV file.

        Each row is converted to a key-value string representation.

        Args:
            content: Raw CSV bytes.
            filename: Original filename for logging.

        Returns:
            Row-by-row text representation of the CSV data.

        Raises:
            ValueError: If the CSV cannot be parsed.
        """
        try:
            df = pd.read_csv(BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Failed to parse CSV '{filename}': {exc}") from exc

        if df.empty:
            raise ValueError(f"CSV '{filename}' contains no data rows")

        rows: list[str] = []
        columns = list(df.columns)

        for idx, row in df.iterrows():
            parts = []
            for col in columns:
                val = row[col]
                if pd.notna(val):
                    parts.append(f"{col}: {val}")
            if parts:
                rows.append(" | ".join(parts))

        full_text = "\n".join(rows)

        logger.info("Extracted %d rows from '%s'", len(rows), filename)
        return full_text
