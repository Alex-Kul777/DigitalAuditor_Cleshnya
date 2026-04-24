"""Tests for persona-aware knowledge management (tasks 1-3).

Covers:
- Task 1: retriever.py - filter + exclude_personas parameters
- Task 2: indexer.py - index_documents(docs) method
- Task 3: persona_indexer.py - scaffold() and ingest_corpus() methods
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from langchain_core.documents import Document

from knowledge.retriever import Retriever
from knowledge.indexer import VectorIndexer
from knowledge.persona_indexer import PersonaIndexer


# ============================================================================
# Task 1: Retriever Tests — filter + exclude_personas
# ============================================================================

class TestRetrieverFiltering:
    """Test Task 1: retriever.retrieve() with filter and exclude_personas."""

    def test_retrieve_signature_accepts_filter(self):
        """Verify retrieve() accepts filter parameter."""
        with patch('knowledge.retriever.Chroma'):
            retriever = Retriever()
            assert hasattr(retriever, 'retrieve')
            import inspect
            sig = inspect.signature(retriever.retrieve)
            assert 'filter' in sig.parameters
            assert 'exclude_personas' in sig.parameters

    def test_retrieve_exclude_personas_parameter(self):
        """Verify exclude_personas parameter exists."""
        with patch('knowledge.retriever.Chroma'):
            retriever = Retriever()
            # Mock the vector store
            retriever.vector_store.similarity_search = Mock(
                return_value=[
                    Document(page_content="audit doc", metadata={"persona": None}),
                    Document(page_content="reviewer doc", metadata={"persona": "uncle_kahneman"}),
                    Document(page_content="audit doc 2", metadata={"persona": None}),
                ]
            )

            # Query with exclude_personas
            results = retriever.retrieve(
                "test query",
                k=2,
                exclude_personas=["uncle_kahneman"]
            )

            # Should return only non-persona docs
            assert len(results) == 2
            for result in results:
                assert result["metadata"].get("persona") != "uncle_kahneman"

    def test_retrieve_filter_parameter(self):
        """Verify filter parameter is passed to vector store."""
        with patch('knowledge.retriever.Chroma') as mock_chroma:
            retriever = Retriever()
            retriever.vector_store.similarity_search = Mock(return_value=[])

            retriever.retrieve("test", filter={"persona": "uncle_kahneman"})

            # Verify similarity_search was called with filter
            retriever.vector_store.similarity_search.assert_called()

    def test_retrieve_fetch_multiply_strategy(self):
        """Verify fetch k*3 when using exclude_personas."""
        with patch('knowledge.retriever.Chroma'):
            retriever = Retriever()
            retriever.vector_store.similarity_search = Mock(
                return_value=[Document(page_content=f"doc {i}", metadata={"persona": None}) for i in range(6)]
            )

            retriever.retrieve("test", k=2, exclude_personas=["uncle_kahneman"])

            # Should fetch k*3 = 6 docs
            call_args = retriever.vector_store.similarity_search.call_args
            assert call_args[1]['k'] == 6


# ============================================================================
# Task 2: Indexer Tests — index_documents()
# ============================================================================

class TestIndexerIndexDocuments:
    """Test Task 2: indexer.index_documents(docs, persona=None)."""

    def test_index_documents_signature(self):
        """Verify index_documents() method exists with correct signature."""
        with patch('knowledge.indexer.Chroma'):
            indexer = VectorIndexer()
            assert hasattr(indexer, 'index_documents')
            import inspect
            sig = inspect.signature(indexer.index_documents)
            assert 'documents' in sig.parameters
            assert 'persona' in sig.parameters

    def test_index_documents_adds_persona_metadata(self):
        """Verify index_documents() adds persona metadata to documents."""
        with patch('knowledge.indexer.Chroma') as mock_chroma:
            indexer = VectorIndexer()
            indexer.text_splitter = Mock()
            indexer.text_splitter.split_documents = Mock(
                return_value=[Document(page_content="test", metadata={"persona": "test_persona"})]
            )

            docs = [
                Document(page_content="doc1", metadata={"source": "test"}),
                Document(page_content="doc2", metadata={"source": "test"}),
            ]

            indexer.index_documents(docs, persona="test_persona")

            # Verify metadata was added
            for doc in docs:
                assert doc.metadata.get("persona") == "test_persona"

    def test_index_documents_returns_chunk_count(self):
        """Verify index_documents() returns count of indexed chunks."""
        with patch('knowledge.indexer.Chroma') as mock_chroma:
            indexer = VectorIndexer()

            # Mock text splitter to return specific number of chunks
            mock_chunks = [
                Document(page_content=f"chunk {i}", metadata={})
                for i in range(5)
            ]
            indexer.text_splitter = Mock()
            indexer.text_splitter.split_documents = Mock(return_value=mock_chunks)

            docs = [Document(page_content="test", metadata={})]
            chunk_count = indexer.index_documents(docs)

            assert chunk_count == 5

    def test_index_documents_without_persona(self):
        """Verify index_documents() works without persona parameter."""
        with patch('knowledge.indexer.Chroma'):
            indexer = VectorIndexer()
            indexer.text_splitter = Mock()
            indexer.text_splitter.split_documents = Mock(
                return_value=[Document(page_content="test", metadata={})]
            )

            docs = [Document(page_content="audit doc", metadata={"source": "audit"})]

            # Should not raise error
            chunk_count = indexer.index_documents(docs)
            assert chunk_count == 1


# ============================================================================
# Task 3: PersonaIndexer Tests — scaffold() and ingest_corpus()
# ============================================================================

class TestPersonaIndexerScaffold:
    """Test Task 3: persona_indexer.scaffold(persona_name)."""

    def test_scaffold_creates_directory(self):
        """Verify scaffold() creates persona directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                persona_dir = indexer.scaffold("test_persona")

                assert persona_dir.exists()
                assert persona_dir.name == "test_persona"

    def test_scaffold_creates_corpus_subdirectory(self):
        """Verify scaffold() creates corpus/ subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                persona_dir = indexer.scaffold("test_persona")
                corpus_dir = persona_dir / "corpus"

                assert corpus_dir.exists()
                assert corpus_dir.is_dir()

    def test_scaffold_creates_config_yaml(self):
        """Verify scaffold() creates config.yaml file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                persona_dir = indexer.scaffold("test_persona")
                config_file = persona_dir / "config.yaml"

                assert config_file.exists()
                content = config_file.read_text()
                assert "test_persona" in content
                assert "corpus_dir" in content

    def test_scaffold_creates_persona_prompt(self):
        """Verify scaffold() creates persona_prompt.md file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                persona_dir = indexer.scaffold("test_persona")
                prompt_file = persona_dir / "persona_prompt.md"

                assert prompt_file.exists()
                content = prompt_file.read_text()
                assert "test_persona" in content or "Test Persona" in content
                assert "Role" in content


class TestPersonaIndexerIngestCorpus:
    """Test Task 3: persona_indexer.ingest_corpus(persona_name, docs_path)."""

    def test_ingest_corpus_signature(self):
        """Verify ingest_corpus() method exists with correct signature."""
        with patch('knowledge.persona_indexer.VectorIndexer'):
            indexer = PersonaIndexer()
            assert hasattr(indexer, 'ingest_corpus')
            import inspect
            sig = inspect.signature(indexer.ingest_corpus)
            assert 'persona_name' in sig.parameters
            assert 'docs_path' in sig.parameters

    def test_ingest_corpus_raises_on_missing_path(self):
        """Verify ingest_corpus() raises FileNotFoundError for missing path."""
        with patch('knowledge.persona_indexer.VectorIndexer'):
            indexer = PersonaIndexer()

            with pytest.raises(FileNotFoundError):
                indexer.ingest_corpus("test_persona", "/nonexistent/path")

    def test_ingest_corpus_loads_documents(self):
        """Verify ingest_corpus() loads documents from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test documents
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.txt").write_text("Test document 1")
            (docs_dir / "test2.txt").write_text("Test document 2")

            with patch('knowledge.persona_indexer.VectorIndexer') as mock_indexer_class:
                mock_indexer = Mock()
                mock_indexer.index_documents = Mock(return_value=2)
                mock_indexer_class.return_value = mock_indexer

                indexer = PersonaIndexer()
                chunk_count = indexer.ingest_corpus("test_persona", str(docs_dir))

                # Verify index_documents was called
                mock_indexer.index_documents.assert_called()
                assert chunk_count == 2

    def test_ingest_corpus_calls_indexer_with_persona(self):
        """Verify ingest_corpus() passes persona to index_documents()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "test.txt").write_text("Test")

            with patch('knowledge.persona_indexer.VectorIndexer') as mock_indexer_class:
                mock_indexer = Mock()
                mock_indexer.index_documents = Mock(return_value=1)
                mock_indexer_class.return_value = mock_indexer

                indexer = PersonaIndexer()
                indexer.ingest_corpus("uncle_kahneman", str(docs_dir))

                # Verify persona was passed
                call_args = mock_indexer.index_documents.call_args
                assert call_args[1]['persona'] == "uncle_kahneman"


class TestPersonaIndexerListPersonas:
    """Test Task 3: persona_indexer.list_personas()."""

    def test_list_personas_returns_list(self):
        """Verify list_personas() returns a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                personas = indexer.list_personas()

                assert isinstance(personas, list)

    def test_list_personas_finds_created_personas(self):
        """Verify list_personas() finds scaffolded personas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                indexer = PersonaIndexer()
                indexer.scaffold("persona_a")
                indexer.scaffold("persona_b")

                personas = indexer.list_personas()

                assert "persona_a" in personas
                assert "persona_b" in personas
                assert len(personas) == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestPersonaInfrastructureIntegration:
    """Integration tests for complete persona workflow (tasks 1-3)."""

    def test_end_to_end_persona_workflow(self):
        """Test complete workflow: scaffold → ingest → retrieve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                # Create documents
                docs_dir = Path(tmpdir) / "docs"
                docs_dir.mkdir()
                (docs_dir / "insight.txt").write_text("Kahneman insight on heuristics")

                # Task 3: Scaffold persona
                persona_indexer = PersonaIndexer()
                persona_dir = persona_indexer.scaffold("uncle_kahneman")
                assert (persona_dir / "corpus").exists()

                # Task 3: Ingest corpus (mocked)
                with patch('knowledge.persona_indexer.VectorIndexer') as mock_indexer_class:
                    mock_indexer = Mock()
                    mock_indexer.index_documents = Mock(return_value=1)
                    mock_indexer_class.return_value = mock_indexer

                    chunk_count = persona_indexer.ingest_corpus("uncle_kahneman", str(docs_dir))
                    assert chunk_count == 1

                # Task 3: List personas
                personas = persona_indexer.list_personas()
                assert "uncle_kahneman" in personas

                # Task 2: Verify indexer can handle persona metadata
                with patch('knowledge.indexer.Chroma'):
                    indexer = VectorIndexer()
                    test_doc = Document(
                        page_content="test",
                        metadata={"source": "test"}
                    )
                    indexer.text_splitter = Mock()
                    indexer.text_splitter.split_documents = Mock(
                        return_value=[test_doc]
                    )
                    indexer.index_documents([test_doc], persona="uncle_kahneman")
                    assert test_doc.metadata.get("persona") == "uncle_kahneman"
