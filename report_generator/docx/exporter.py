"""DOCX exporter: MD → DOCX with reviewer comments injected."""

from pathlib import Path
from typing import List, Tuple
import re

from core.logger import setup_logger
from report_generator.docx.backends import DocxBackend, get_backend, CommentRecord

logger = setup_logger("docx.exporter")


class DocxExporter:
    """Export Markdown audit report to DOCX with persona comments as Word comments."""

    def __init__(self, backend: DocxBackend = None):
        """Initialize exporter with backend.

        Args:
            backend: DocxBackend instance. If None, auto-select via get_backend("auto")
        """
        self.backend = backend or get_backend("auto")
        logger.info(f"DocxExporter initialized with {self.backend.__class__.__name__}")

    def export(self, md_path: Path, output_path: Path) -> Path:
        """Export Markdown to DOCX with reviewer comments.

        Process:
        1. Parse MD, extract <!-- REVIEWER:<name>:START --> blocks
        2. Strip reviewer blocks from MD → clean_md
        3. backend.md_to_docx(clean_md, output_path)
        4. For each extracted comment → backend.add_comment(anchor, text, author)

        Args:
            md_path: Path to Markdown source file
            output_path: Path to write DOCX output

        Returns:
            output_path
        """
        if not md_path.exists():
            raise FileNotFoundError(f"MD file not found: {md_path}")

        md_content = md_path.read_text(encoding='utf-8')

        # Extract reviewer comment blocks
        comments = self._extract_comments(md_content)
        logger.debug(f"Extracted {len(comments)} reviewer comments")

        # Strip reviewer blocks from markdown
        clean_md = self._strip_comments(md_content)

        # Convert clean MD to DOCX
        self.backend.md_to_docx(clean_md, output_path)
        logger.info(f"DOCX written: {output_path}")

        # Inject comments into DOCX
        for anchor, author, comment_text in comments:
            try:
                self.backend.add_comment(output_path, anchor, comment_text, author)
            except Exception as e:
                logger.warning(f"Failed to add comment by {author}: {e}")

        logger.info(f"Export complete: {output_path} ({len(comments)} comments)")
        return output_path

    def _extract_comments(self, md: str) -> List[Tuple[str, str, str]]:
        """Extract reviewer comment blocks from markdown.

        Returns:
            List of (anchor_text, author, comment_text) tuples
        """
        pattern = r'<!-- REVIEWER:(\w+):START -->(.*?)<!-- REVIEWER:\w+:END -->'
        matches = re.findall(pattern, md, re.DOTALL)

        comments = []
        for author, comment_html in matches:
            # Extract comment text (strip HTML comment markers, preserve markdown)
            comment_text = comment_html.strip()
            if comment_text.startswith('\n'):
                comment_text = comment_text[1:]
            if comment_text.endswith('\n'):
                comment_text = comment_text[:-1]

            # Find anchor: last 80 chars of preceding non-comment paragraph
            anchor = self._find_anchor(md, author, comment_html)
            comments.append((anchor, author, comment_text))

        return comments

    def _find_anchor(self, md: str, author: str, comment_block: str) -> str:
        """Find anchor text (preceding paragraph) for comment."""
        # Find position of comment block in markdown
        comment_start = md.find(f"<!-- REVIEWER:{author}:START -->")
        if comment_start == -1:
            return "[No anchor found]"

        # Get text before comment block
        before_comment = md[:comment_start].rstrip()

        # Find last non-empty paragraph
        paragraphs = re.split(r'\n\s*\n', before_comment)
        for para in reversed(paragraphs):
            para = para.strip()
            if para and not para.startswith('#') and not para.startswith('|'):
                # Return last 80 chars as anchor
                return para[-80:] if len(para) > 80 else para

        return "[No paragraph anchor]"

    def _strip_comments(self, md: str) -> str:
        """Remove all reviewer comment blocks from markdown."""
        pattern = r'\n?<!-- REVIEWER:\w+:START -->.*?<!-- REVIEWER:\w+:END -->\n?'
        return re.sub(pattern, '', md, flags=re.DOTALL)
