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


class TestPersonaScaffoldingTask5:
    """Test Task 5: personas/_templates/ and personas/uncle_kahneman/ structure."""

    def test_templates_directory_exists(self):
        """Verify personas/_templates/ directory exists."""
        from core.config import PROJECT_ROOT
        templates_dir = PROJECT_ROOT / "personas" / "_templates"
        assert templates_dir.exists(), f"Templates dir missing: {templates_dir}"
        assert templates_dir.is_dir()

    def test_templates_config_exists(self):
        """Verify personas/_templates/config.yaml exists and is valid."""
        from core.config import PROJECT_ROOT
        config_file = PROJECT_ROOT / "personas" / "_templates" / "config.yaml"
        assert config_file.exists(), f"Template config missing: {config_file}"
        content = config_file.read_text()
        assert "name:" in content
        assert "description:" in content
        assert "corpus_dir:" in content

    def test_templates_prompt_exists(self):
        """Verify personas/_templates/persona_prompt.md exists."""
        from core.config import PROJECT_ROOT
        prompt_file = PROJECT_ROOT / "personas" / "_templates" / "persona_prompt.md"
        assert prompt_file.exists(), f"Template prompt missing: {prompt_file}"
        content = prompt_file.read_text()
        assert "Role" in content
        assert "Expertise" in content

    def test_templates_corpus_directory(self):
        """Verify personas/_templates/corpus/ directory exists."""
        from core.config import PROJECT_ROOT
        corpus_dir = PROJECT_ROOT / "personas" / "_templates" / "corpus"
        assert corpus_dir.exists(), f"Template corpus dir missing: {corpus_dir}"
        assert corpus_dir.is_dir()

    def test_uncle_kahneman_directory_exists(self):
        """Verify personas/uncle_kahneman/ directory exists."""
        from core.config import PROJECT_ROOT
        persona_dir = PROJECT_ROOT / "personas" / "uncle_kahneman"
        assert persona_dir.exists(), f"Uncle Kahneman dir missing: {persona_dir}"
        assert persona_dir.is_dir()

    def test_uncle_kahneman_config_exists(self):
        """Verify personas/uncle_kahneman/config.yaml exists and is valid."""
        from core.config import PROJECT_ROOT
        config_file = PROJECT_ROOT / "personas" / "uncle_kahneman" / "config.yaml"
        assert config_file.exists(), f"Uncle Kahneman config missing: {config_file}"
        content = config_file.read_text()
        assert "uncle_kahneman" in content
        assert "behavioral_economics" in content or "decision_making" in content

    def test_uncle_kahneman_prompt_exists(self):
        """Verify personas/uncle_kahneman/persona_prompt.md exists and has content."""
        from core.config import PROJECT_ROOT
        prompt_file = PROJECT_ROOT / "personas" / "uncle_kahneman" / "persona_prompt.md"
        assert prompt_file.exists(), f"Uncle Kahneman prompt missing: {prompt_file}"
        content = prompt_file.read_text()
        assert "Kahneman" in content or "behavioral" in content.lower()
        assert "System 1" in content or "System 2" in content
        assert "Роль" in content or "Role" in content

    def test_uncle_kahneman_corpus_directory(self):
        """Verify personas/uncle_kahneman/corpus/ directory exists."""
        from core.config import PROJECT_ROOT
        corpus_dir = PROJECT_ROOT / "personas" / "uncle_kahneman" / "corpus"
        assert corpus_dir.exists(), f"Uncle Kahneman corpus dir missing: {corpus_dir}"
        assert corpus_dir.is_dir()

    def test_persona_indexer_lists_uncle_kahneman(self):
        """Verify PersonaIndexer.list_personas() finds uncle_kahneman."""
        with patch('knowledge.persona_indexer.PROJECT_ROOT') as mock_root:
            from core.config import PROJECT_ROOT
            mock_root.__truediv__ = lambda self, x: PROJECT_ROOT / x
            mock_root.__str__ = lambda self: str(PROJECT_ROOT)

            indexer = PersonaIndexer()
            personas = indexer.list_personas()

            assert "uncle_kahneman" in personas, f"uncle_kahneman not found in {personas}"


class TestOrchestratorTask6:
    """Test Task 6: report_generator/orchestrator.py — exclude_personas integration."""

    def test_get_context_signature_has_exclude_personas(self):
        """Verify _get_context() accepts exclude_personas parameter."""
        from report_generator.orchestrator import ReportOrchestrator
        import inspect

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever'):
                    orchestrator = ReportOrchestrator(task_dir)
                    sig = inspect.signature(orchestrator._get_context)
                    assert 'exclude_personas' in sig.parameters

    def test_get_context_excludes_all_personas_by_default(self):
        """Verify _get_context() excludes all personas when not specified."""
        from report_generator.orchestrator import ReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever') as mock_retriever_class:
                    mock_retriever = Mock()
                    mock_retriever.retrieve = Mock(return_value=[
                        {"content": "Test document content"}
                    ])
                    mock_retriever_class.return_value = mock_retriever

                    with patch('knowledge.persona_indexer.PROJECT_ROOT') as mock_root:
                        from core.config import PROJECT_ROOT
                        mock_root.__truediv__ = lambda self, x: PROJECT_ROOT / x
                        mock_root.__str__ = lambda self: str(PROJECT_ROOT)

                        orchestrator = ReportOrchestrator(task_dir)
                        context = orchestrator._get_context("test query")

                        # Verify retrieve was called with exclude_personas
                        mock_retriever.retrieve.assert_called()
                        call_kwargs = mock_retriever.retrieve.call_args[1]
                        assert 'exclude_personas' in call_kwargs
                        assert isinstance(call_kwargs['exclude_personas'], list)

    def test_get_context_respects_explicit_exclude_personas(self):
        """Verify _get_context() uses explicit exclude_personas when provided."""
        from report_generator.orchestrator import ReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever') as mock_retriever_class:
                    mock_retriever = Mock()
                    mock_retriever.retrieve = Mock(return_value=[
                        {"content": "Test document"}
                    ])
                    mock_retriever_class.return_value = mock_retriever

                    orchestrator = ReportOrchestrator(task_dir)
                    orchestrator._get_context("test", exclude_personas=["uncle_kahneman"])

                    # Verify retrieve was called with explicit list
                    call_kwargs = mock_retriever.retrieve.call_args[1]
                    assert call_kwargs['exclude_personas'] == ["uncle_kahneman"]

    def test_get_context_returns_concatenated_content(self):
        """Verify _get_context() concatenates document content."""
        from report_generator.orchestrator import ReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever') as mock_retriever_class:
                    mock_retriever = Mock()
                    mock_retriever.retrieve = Mock(return_value=[
                        {"content": "Document 1 content"},
                        {"content": "Document 2 content"}
                    ])
                    mock_retriever_class.return_value = mock_retriever

                    with patch('knowledge.persona_indexer.PersonaIndexer'):
                        orchestrator = ReportOrchestrator(task_dir)
                        context = orchestrator._get_context("test")

                        assert "Document 1 content" in context
                        assert "Document 2 content" in context
                        assert "\n\n" in context  # Documents separated by newlines

    def test_get_context_handles_retrieval_failure(self):
        """Verify _get_context() handles retriever exceptions gracefully."""
        from report_generator.orchestrator import ReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever') as mock_retriever_class:
                    mock_retriever = Mock()
                    mock_retriever.retrieve = Mock(side_effect=Exception("Retriever error"))
                    mock_retriever_class.return_value = mock_retriever

                    orchestrator = ReportOrchestrator(task_dir)
                    context = orchestrator._get_context("test")

                    assert context == ""  # Returns empty string on error

    def test_get_context_truncates_long_documents(self):
        """Verify _get_context() truncates documents to 500 chars."""
        from report_generator.orchestrator import ReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            task_dir.mkdir(exist_ok=True)
            (task_dir / "config.yaml").write_text("company: Test")

            long_content = "x" * 1000

            with patch('report_generator.orchestrator.CisaAuditor'):
                with patch('report_generator.orchestrator.Retriever') as mock_retriever_class:
                    mock_retriever = Mock()
                    mock_retriever.retrieve = Mock(return_value=[
                        {"content": long_content}
                    ])
                    mock_retriever_class.return_value = mock_retriever

                    with patch('knowledge.persona_indexer.PersonaIndexer'):
                        orchestrator = ReportOrchestrator(task_dir)
                        context = orchestrator._get_context("test")

                        assert len(context) == 500
                        assert context == "x" * 500


class TestMainCLITask7:
    """Test Task 7: main.py — build-persona CLI command."""

    def test_build_persona_command_exists(self):
        """Verify build-persona command is registered in CLI."""
        from main import cli

        assert 'build-persona' in [cmd.name for cmd in cli.commands.values()]

    def test_build_persona_command_signature(self):
        """Verify build-persona accepts name argument."""
        from main import cli
        import inspect

        build_persona_cmd = None
        for cmd in cli.commands.values():
            if cmd.name == 'build-persona':
                build_persona_cmd = cmd
                break

        assert build_persona_cmd is not None
        # Check that it has required arguments
        params = {p.name: p for p in build_persona_cmd.params}
        assert 'name' in params
        assert 'corpus' in params

    def test_build_persona_scaffolds_directory(self):
        """Verify build-persona creates persona directory structure."""
        from click.testing import CliRunner
        from main import cli

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                runner = CliRunner()
                result = runner.invoke(cli, ['build-persona', 'test_persona'])

                # Command should succeed
                assert result.exit_code == 0
                assert "Persona 'test_persona' scaffolded" in result.output

    def test_build_persona_with_corpus(self):
        """Verify build-persona can ingest corpus."""
        from click.testing import CliRunner
        from main import cli

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test corpus
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "test.txt").write_text("Test document")

            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                with patch('knowledge.persona_indexer.VectorIndexer') as mock_indexer_class:
                    mock_indexer = Mock()
                    mock_indexer.index_documents = Mock(return_value=1)
                    mock_indexer_class.return_value = mock_indexer

                    runner = CliRunner()
                    result = runner.invoke(cli, [
                        'build-persona', 'test_persona',
                        '--corpus', str(corpus_dir)
                    ])

                    assert result.exit_code == 0
                    assert "Indexed" in result.output

    def test_build_persona_handles_missing_corpus(self):
        """Verify build-persona handles missing corpus path."""
        from click.testing import CliRunner
        from main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            'build-persona', 'test_persona',
            '--corpus', '/nonexistent/corpus'
        ])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_build_persona_lists_all_personas(self):
        """Verify build-persona lists available personas after creation."""
        from click.testing import CliRunner
        from main import cli

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('knowledge.persona_indexer.PROJECT_ROOT', Path(tmpdir)):
                runner = CliRunner()
                result = runner.invoke(cli, ['build-persona', 'new_persona'])

                assert result.exit_code == 0
                assert "Available personas:" in result.output
