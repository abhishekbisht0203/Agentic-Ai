"""
Base document loader abstraction.

Provides the abstract base class and factory for all document loaders
that extract text content from various file formats.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    async def load(self, content: bytes, filename: str) -> str:
        """Load and extract text from document content.

        Args:
            content: Raw file bytes.
            filename: Original filename (used for format detection).

        Returns:
            Extracted plain text.
        """
        ...

    @staticmethod
    def detect_loader(filename: str, content_type: str) -> "BaseDocumentLoader":
        """Factory to select the right loader based on file type.

        Args:
            filename: Original filename.
            content_type: MIME type of the file.

        Returns:
            An instantiated loader for the detected format.

        Raises:
            ValueError: If no loader matches the file type.
        """
        from app.rag.loaders.pdf_loader import PDFLoader
        from app.rag.loaders.docx_loader import DOCXLoader
        from app.rag.loaders.csv_loader import CSVLoader
        from app.rag.loaders.text_loader import TextLoader
        from app.rag.loaders.html_loader import HTMLLoader
        from app.rag.loaders.pptx_loader import PPTXLoader

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        loader_map: dict[str, type[BaseDocumentLoader]] = {
            "pdf": PDFLoader,
            "docx": DOCXLoader,
            "doc": DOCXLoader,
            "csv": CSVLoader,
            "txt": TextLoader,
            "md": TextLoader,
            "markdown": TextLoader,
            "html": HTMLLoader,
            "htm": HTMLLoader,
            "pptx": PPTXLoader,
            "ppt": PPTXLoader,
        }

        mime_map: dict[str, type[BaseDocumentLoader]] = {
            "application/pdf": PDFLoader,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXLoader,
            "text/csv": CSVLoader,
            "text/plain": TextLoader,
            "text/html": HTMLLoader,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": PPTXLoader,
        }

        if ext in loader_map:
            loader_cls = loader_map[ext]
            logger.debug("Detected loader %s for extension '%s'", loader_cls.__name__, ext)
            return loader_cls()

        if content_type in mime_map:
            loader_cls = mime_map[content_type]
            logger.debug("Detected loader %s for content type '%s'", loader_cls.__name__, content_type)
            return loader_cls()

        raise ValueError(
            f"No loader found for file '{filename}' with content type '{content_type}'. "
            f"Supported extensions: {list(loader_map.keys())}"
        )
