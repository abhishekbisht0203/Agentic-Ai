"""
Document loaders package.

Provides loaders for various document formats used in the RAG pipeline.
"""

from app.rag.loaders.base import BaseDocumentLoader
from app.rag.loaders.pdf_loader import PDFLoader
from app.rag.loaders.docx_loader import DOCXLoader
from app.rag.loaders.csv_loader import CSVLoader
from app.rag.loaders.text_loader import TextLoader
from app.rag.loaders.html_loader import HTMLLoader
from app.rag.loaders.pptx_loader import PPTXLoader
from app.rag.loaders.web_loader import WebPageLoader
from app.rag.loaders.youtube_loader import YouTubeLoader

__all__ = [
    "BaseDocumentLoader",
    "PDFLoader",
    "DOCXLoader",
    "CSVLoader",
    "TextLoader",
    "HTMLLoader",
    "PPTXLoader",
    "WebPageLoader",
    "YouTubeLoader",
]
