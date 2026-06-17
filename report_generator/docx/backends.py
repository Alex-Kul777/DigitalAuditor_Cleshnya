"""Adapter layer for DOCX libraries: python-docx, docx-editor, docx-revisions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging

from core.logger import setup_logger

logger = setup_logger("docx.backends")

# Conditional imports
try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False

try:
    import docx_editor
    HAS_DOCX_EDITOR = True
except ImportError:
    HAS_DOCX_EDITOR = False

try:
    import docx_revisions
    HAS_DOCX_REVISIONS = True
except ImportError:
    HAS_DOCX_REVISIONS = False


@dataclass
class CommentRecord:
    """Represents a comment extracted from DOCX."""
    anchor_text: str
    comment_text: str
    author: str
    timestamp: Optional[str] = None


@dataclass
class RevisionRecord:
    """Represents a tracked change (insertion/deletion) from DOCX."""
    old_text: str
    new_text: str
    author: str
    timestamp: Optional[str] = None
    change_type: str = "unknown"  # "insertion", "deletion", "replacement"


class DocxBackend(ABC):
    """Abstract base class for DOCX operations."""

    @abstractmethod
    def md_to_docx(self, md: str, output_path: Path) -> None:
        """Convert Markdown to DOCX."""
        pass

    @abstractmethod
    def add_comment(self, docx_path: Path, anchor_text: str, comment: str, author: str) -> None:
        """Add comment to DOCX at anchor location."""
        pass

    @abstractmethod
    def add_tracked_change(self, docx_path: Path, old_text: str, new_text: str, author: str) -> None:
        """Add tracked change (insertion/deletion) to DOCX."""
        pass

    @abstractmethod
    def read_comments(self, docx_path: Path) -> List[CommentRecord]:
        """Extract comments from DOCX."""
        pass

    @abstractmethod
    def read_tracked_changes(self, docx_path: Path) -> List[RevisionRecord]:
        """Extract tracked changes from DOCX."""
        pass


class PythonDocxBackend(DocxBackend):
    """python-docx backend: basic MD→DOCX + simple comments."""

    def __init__(self):
        if not HAS_PYTHON_DOCX:
            raise ImportError("python-docx not installed. pip install python-docx")
        logger.info("PythonDocxBackend initialized")

    def md_to_docx(self, md: str, output_path: Path) -> None:
        """Convert Markdown to DOCX using basic conversion."""
        try:
            from markdownify import markdownify as md_to_html
        except ImportError:
            logger.warning("markdownify not available, using plaintext conversion")
            md_to_html = None

        doc = Document()

        # Simple markdown parsing: headings, paragraphs, lists
        for line in md.split('\n'):
            line = line.rstrip()
            if not line:
                continue

            if line.startswith('# '):
                p = doc.add_paragraph(line[2:], style='Heading 1')
            elif line.startswith('## '):
                p = doc.add_paragraph(line[3:], style='Heading 2')
            elif line.startswith('### '):
                p = doc.add_paragraph(line[4:], style='Heading 3')
            elif line.startswith('- '):
                p = doc.add_paragraph(line[2:], style='List Bullet')
            elif line.startswith('| '):
                # Simple table indicator (skip for now, handle as text)
                doc.add_paragraph(line)
            else:
                doc.add_paragraph(line)

        doc.save(str(output_path))
        logger.info(f"DOCX written to {output_path}")

    def add_comment(self, docx_path: Path, anchor_text: str, comment: str, author: str) -> None:
        """Add comment using basic python-docx approach (footer-based, limited)."""
        doc = Document(str(docx_path))

        # Find paragraph containing anchor_text
        for i, para in enumerate(doc.paragraphs):
            if anchor_text in para.text:
                # Add comment as next paragraph (basic approach)
                # Note: True DOCX comments require XML manipulation; this is fallback
                comment_para = doc.paragraphs[i]._element.addnext(
                    doc.paragraphs[i]._element.__class__()
                )
                comment_para = doc.add_paragraph(f"💬 [{author}]: {comment}", style='Normal')
                comment_para.paragraph_format.left_indent = Inches(0.5)
                break

        doc.save(str(docx_path))
        logger.debug(f"Comment added by {author}")

    def add_tracked_change(self, docx_path: Path, old_text: str, new_text: str, author: str) -> None:
        """Add tracked change (not fully supported in python-docx)."""
        logger.warning("add_tracked_change not supported by PythonDocxBackend (requires docx-revisions)")
        # Fallback: add as strikethrough + new text
        doc = Document(str(docx_path))
        for para in doc.paragraphs:
            if old_text in para.text:
                para.text = para.text.replace(old_text, f"~~{old_text}~~ {new_text}")
                break
        doc.save(str(docx_path))

    def read_comments(self, docx_path: Path) -> List[CommentRecord]:
        """Extract comments from DOCX (basic support)."""
        doc = Document(str(docx_path))
        comments = []

        # Look for comment-like paragraphs (marked with 💬 or [Author]:)
        for para in doc.paragraphs:
            if para.text.startswith('💬 ['):
                # Parse "💬 [Author]: comment_text"
                rest = para.text[4:]  # Remove "💬 "
                if ']:' in rest:
                    author, comment_text = rest.split(']:', 1)
                    author = author[1:]  # Remove leading [
                    comments.append(CommentRecord(
                        anchor_text="",
                        comment_text=comment_text.strip(),
                        author=author.strip()
                    ))

        return comments

    def read_tracked_changes(self, docx_path: Path) -> List[RevisionRecord]:
        """Extract tracked changes from DOCX (not supported)."""
        logger.warning("read_tracked_changes not supported by PythonDocxBackend")
        return []


class DocxEditorBackend(DocxBackend):
    """docx-editor backend: hash-anchored comment injection."""

    def __init__(self):
        if not HAS_DOCX_EDITOR:
            logger.warning("docx-editor not installed. pip install docx-editor")
        logger.info("DocxEditorBackend initialized (preview, limited)")

    def md_to_docx(self, md: str, output_path: Path) -> None:
        """Fallback to PythonDocxBackend for MD→DOCX."""
        backend = PythonDocxBackend()
        backend.md_to_docx(md, output_path)
        logger.debug("md_to_docx delegated to PythonDocxBackend")

    def add_comment(self, docx_path: Path, anchor_text: str, comment: str, author: str) -> None:
        """Add hash-anchored comment (docx-editor feature)."""
        if not HAS_DOCX_EDITOR:
            logger.warning("docx-editor not available, fallback to PythonDocxBackend")
            backend = PythonDocxBackend()
            backend.add_comment(docx_path, anchor_text, comment, author)
            return

        logger.debug(f"add_comment via docx-editor for anchor: {anchor_text[:50]}")
        # TODO: integrate docx_editor.add_comment() API when docs available
        # Placeholder: fallback to python-docx
        backend = PythonDocxBackend()
        backend.add_comment(docx_path, anchor_text, comment, author)

    def add_tracked_change(self, docx_path: Path, old_text: str, new_text: str, author: str) -> None:
        """Add tracked change (limited support in docx-editor)."""
        logger.warning("add_tracked_change partially supported by DocxEditorBackend")
        backend = PythonDocxBackend()
        backend.add_tracked_change(docx_path, old_text, new_text, author)

    def read_comments(self, docx_path: Path) -> List[CommentRecord]:
        """Extract comments using docx-editor."""
        if not HAS_DOCX_EDITOR:
            logger.debug("docx-editor fallback to PythonDocxBackend")
            backend = PythonDocxBackend()
            return backend.read_comments(docx_path)

        logger.debug("read_comments via docx-editor")
        # TODO: integrate docx_editor.read_comments() when docs available
        backend = PythonDocxBackend()
        return backend.read_comments(docx_path)

    def read_tracked_changes(self, docx_path: Path) -> List[RevisionRecord]:
        """Extract tracked changes using docx-editor."""
        if not HAS_DOCX_EDITOR:
            logger.debug("docx-editor not available")
            return []

        logger.debug("read_tracked_changes via docx-editor")
        # TODO: integrate docx_editor.read_tracked_changes() when docs available
        return []


class DocxRevisionsBackend(DocxBackend):
    """docx-revisions backend: <w:ins>/<w:del> R/W via XML."""

    def __init__(self):
        if not HAS_DOCX_REVISIONS:
            logger.warning("docx-revisions not installed. pip install docx-revisions")
        logger.info("DocxRevisionsBackend initialized (preview, limited)")

    def md_to_docx(self, md: str, output_path: Path) -> None:
        """Fallback to PythonDocxBackend for MD→DOCX."""
        backend = PythonDocxBackend()
        backend.md_to_docx(md, output_path)
        logger.debug("md_to_docx delegated to PythonDocxBackend")

    def add_comment(self, docx_path: Path, anchor_text: str, comment: str, author: str) -> None:
        """Fallback to PythonDocxBackend (docx-revisions focuses on tracked changes)."""
        backend = PythonDocxBackend()
        backend.add_comment(docx_path, anchor_text, comment, author)

    def add_tracked_change(self, docx_path: Path, old_text: str, new_text: str, author: str) -> None:
        """Add tracked change using XML <w:ins>/<w:del>."""
        if not HAS_DOCX_REVISIONS:
            logger.warning("docx-revisions not available, fallback")
            backend = PythonDocxBackend()
            backend.add_tracked_change(docx_path, old_text, new_text, author)
            return

        logger.debug(f"add_tracked_change via docx-revisions: {old_text[:30]} → {new_text[:30]}")
        # TODO: integrate docx_revisions API when docs available
        # Placeholder: fallback to python-docx
        backend = PythonDocxBackend()
        backend.add_tracked_change(docx_path, old_text, new_text, author)

    def read_comments(self, docx_path: Path) -> List[CommentRecord]:
        """Extract comments (fallback to python-docx)."""
        backend = PythonDocxBackend()
        return backend.read_comments(docx_path)

    def read_tracked_changes(self, docx_path: Path) -> List[RevisionRecord]:
        """Extract tracked changes using XML parsing."""
        if not HAS_DOCX_REVISIONS:
            logger.debug("docx-revisions not available")
            return []

        logger.debug("read_tracked_changes via docx-revisions")
        # TODO: integrate docx_revisions.extract_revisions() when docs available
        return []


def get_backend(name: str = "auto") -> DocxBackend:
    """Get DOCX backend by name.

    Args:
        name: "auto" (best-fit), "python_docx", "docx_editor", "docx_revisions"

    Returns:
        DocxBackend instance

    Raises:
        ValueError: if backend not available
    """
    if name == "auto":
        # Auto-select best-fit: prefer docx-revisions for full features, fallback chain
        if HAS_PYTHON_DOCX:
            logger.info("Backend selected: auto → PythonDocxBackend (fallback available)")
            return PythonDocxBackend()
        else:
            raise ValueError("No DOCX backend available. Install python-docx")

    elif name == "python_docx":
        return PythonDocxBackend()
    elif name == "docx_editor":
        return DocxEditorBackend()
    elif name == "docx_revisions":
        return DocxRevisionsBackend()
    else:
        raise ValueError(f"Unknown backend: {name}. Choose: auto, python_docx, docx_editor, docx_revisions")
