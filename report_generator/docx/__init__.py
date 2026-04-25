"""DOCX export, import, and versioning for audit reports."""

from report_generator.docx.backends import (
    DocxBackend,
    PythonDocxBackend,
    DocxEditorBackend,
    DocxRevisionsBackend,
    get_backend,
)
from report_generator.docx.exporter import DocxExporter
from report_generator.docx.importer import DocxImporter, Feedback
from report_generator.docx.version_manager import VersionManager

__all__ = [
    "DocxBackend",
    "PythonDocxBackend",
    "DocxEditorBackend",
    "DocxRevisionsBackend",
    "get_backend",
    "DocxExporter",
    "DocxImporter",
    "Feedback",
    "VersionManager",
]
