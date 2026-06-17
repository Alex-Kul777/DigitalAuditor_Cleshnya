"""Brink's Modern Internal Auditing PDF indexing with chapter filtering."""
import json
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import EMBEDDING_MODEL, CHROMA_DB_PATH, BRINKS_CHUNK_SIZE, BRINKS_CHAPTERS_INDEX, PROJECT_ROOT
from core.logger import setup_logger


class BrinksIndexer:
    """Index Brink's PDF with chapter-based filtering and RAG flags."""

    def __init__(self):
        self.logger = setup_logger("brinks_indexer")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=BRINKS_CHUNK_SIZE,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.chapters_config = self._load_chapters_config()

    def _load_chapters_config(self) -> dict:
        """Load brinks_chapters.json configuration."""
        config_path = PROJECT_ROOT / BRINKS_CHAPTERS_INDEX
        if not config_path.exists():
            self.logger.error(f"Chapters config not found: {config_path}")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_page_range(self, pages_str: str) -> tuple:
        """Parse page range string like '51-100' into (51, 100)."""
        try:
            start, end = pages_str.split('-')
            return int(start.strip()), int(end.strip())
        except (ValueError, AttributeError):
            self.logger.warning(f"Invalid page range: {pages_str}")
            return None, None

    def index_brinks(self, pdf_path: str = None) -> dict:
        """Index Brink's PDF with chapter filtering.

        Args:
            pdf_path: Optional override for PDF file path

        Returns:
            Dict with indexing results: {chapter_num: chunks_indexed}
        """
        # Determine PDF path
        if pdf_path is None:
            config = self.chapters_config.get('brinks_modern_internal_auditing', {})
            pdf_path = config.get('pdf_path')
            if not pdf_path:
                self.logger.error("PDF path not specified and not in config")
                return {}

        pdf_file = PROJECT_ROOT / pdf_path
        if not pdf_file.exists():
            self.logger.error(f"PDF not found: {pdf_file}")
            return {}

        self.logger.info(f"Loading PDF: {pdf_file}")

        # Load all pages from PDF
        try:
            loader = PyPDFLoader(str(pdf_file))
            all_documents = loader.load()
        except Exception as e:
            self.logger.error(f"Failed to load PDF: {e}")
            return {}

        self.logger.info(f"Loaded {len(all_documents)} pages from PDF")

        # Filter and process chapters
        results = {}
        config = self.chapters_config.get('brinks_modern_internal_auditing', {})
        chapters = config.get('chapters', [])

        for chapter in chapters:
            if not chapter.get('include_in_rag', False):
                self.logger.debug(f"Skipping chapter {chapter['number']}: include_in_rag=false")
                continue

            chapter_num = chapter.get('number')
            pages_str = chapter.get('pages')
            title = chapter.get('title', f"Chapter {chapter_num}")
            priority = chapter.get('priority', 'normal')

            # Parse page range
            start_page, end_page = self._parse_page_range(pages_str)
            if start_page is None:
                self.logger.warning(f"Skipping chapter {chapter_num}: invalid page range")
                continue

            # Extract documents for this chapter (pages are 0-indexed in PDF)
            chapter_docs = [
                doc for doc in all_documents
                if start_page <= doc.metadata.get('page', 0) + 1 <= end_page
            ]

            if not chapter_docs:
                self.logger.warning(f"No pages found for chapter {chapter_num} (pages {start_page}-{end_page})")
                continue

            self.logger.info(f"Processing chapter {chapter_num}: {title} ({len(chapter_docs)} pages)")

            # Split into chunks
            chunks = self.text_splitter.split_documents(chapter_docs)

            # Add metadata
            for chunk in chunks:
                if chunk.metadata is None:
                    chunk.metadata = {}
                chunk.metadata.update({
                    'doc_type': 'audit_standard',
                    'req_level': 2,
                    'authority': "Brink's",
                    'chapter_number': chapter_num,
                    'chapter_title': title,
                    'priority': priority,
                    'source_filename': 'brink_s-modern-internal-auditing-7th-edition.pdf'
                })

            # Index chunks
            try:
                vector_store = Chroma(
                    persist_directory=str(CHROMA_DB_PATH),
                    embedding_function=self.embeddings
                )
                vector_store.add_documents(chunks)
                results[chapter_num] = len(chunks)
                self.logger.info(f"Indexed {len(chunks)} chunks for chapter {chapter_num}")
            except Exception as e:
                self.logger.error(f"Failed to index chapter {chapter_num}: {e}")
                results[chapter_num] = 0

        total_chunks = sum(results.values())
        self.logger.info(f"Brink's indexing complete: {len(results)} chapters, {total_chunks} total chunks")
        return results

    def get_indexed_chapters(self) -> list:
        """Get list of chapters with include_in_rag=true."""
        config = self.chapters_config.get('brinks_modern_internal_auditing', {})
        chapters = config.get('chapters', [])
        return [
            {
                'number': ch.get('number'),
                'title': ch.get('title'),
                'priority': ch.get('priority', 'normal')
            }
            for ch in chapters
            if ch.get('include_in_rag', False)
        ]
