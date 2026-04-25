from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from core.config import PROJECT_ROOT
from core.logger import setup_logger
from knowledge.indexer import VectorIndexer
from knowledge.brinks_indexer import BrinksIndexer


class PersonaIndexer:
    """CLI facade for persona-aware document management."""

    def __init__(self):
        self.logger = setup_logger("persona_indexer")
        self.indexer = VectorIndexer()
        self.personas_dir = PROJECT_ROOT / "personas"

    def scaffold(self, persona_name: str) -> Path:
        """Create directory structure for a new persona.

        Args:
            persona_name: Name of the persona (e.g., 'uncle_kahneman')

        Returns:
            Path to created persona directory
        """
        self.logger.info(f"Scaffolding persona: {persona_name}")

        persona_dir = self.personas_dir / persona_name
        persona_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (persona_dir / "corpus").mkdir(exist_ok=True)

        # Create config.yaml
        config_path = persona_dir / "config.yaml"
        if not config_path.exists():
            config_path.write_text(f"""# Persona Configuration: {persona_name}
name: {persona_name}
description: ""
system_prompt_file: persona_prompt.md
corpus_dir: corpus/
""")
            self.logger.debug(f"Created {config_path}")

        # Create persona_prompt.md template
        prompt_path = persona_dir / "persona_prompt.md"
        if not prompt_path.exists():
            prompt_path.write_text(f"""# {persona_name.replace('_', ' ').title()} Persona Prompt

Define the persona's role, expertise, and behavior.

## Role
[Describe the role and responsibilities]

## Expertise
[List areas of expertise]

## Behavior Guidelines
[Define how this persona should behave and respond]
""")
            self.logger.debug(f"Created {prompt_path}")

        self.logger.info(f"Scaffolded persona directory: {persona_dir}")
        return persona_dir

    def ingest_corpus(self, persona_name: str, docs_path: str = None) -> int:
        """Index documents from a directory for a specific persona.

        Args:
            persona_name: Name of the persona
            docs_path: Path to directory/file containing documents. If None for uncle_robert,
                      auto-detects Brink's PDF from persona directory.

        Returns:
            Number of chunks indexed
        """
        # Auto-detect Brink's PDF for uncle_robert if no corpus provided
        if persona_name == "uncle_robert" and docs_path is None:
            brinks_pdf = self.personas_dir / "uncle_Robert" / "brink_s-modern-internal-auditing-7th-edition.pdf"
            if brinks_pdf.exists():
                self.logger.info(f"Auto-detected Brink's PDF: {brinks_pdf}")
                docs_path = str(brinks_pdf)
            else:
                self.logger.warning(f"Brink's PDF not found at {brinks_pdf}")
                return 0

        if docs_path is None:
            raise ValueError(f"No corpus path provided for '{persona_name}'")

        self.logger.info(f"Ingesting corpus for '{persona_name}' from {docs_path}")

        docs_path = Path(docs_path)
        if not docs_path.exists():
            raise FileNotFoundError(f"Corpus path does not exist: {docs_path}")

        # Special handling for uncle_robert: use Brink's chapter-based indexing
        if persona_name == "uncle_robert" and docs_path.name.lower().startswith("brink"):
            self.logger.info("Using BrinksIndexer for uncle_robert persona")
            brinks_indexer = BrinksIndexer()
            results = brinks_indexer.index_brinks(str(docs_path))
            total_chunks = sum(results.values())
            self.logger.info(f"Indexed {len(results)} Brink's chapters ({total_chunks} chunks total)")
            return total_chunks

        # Generic document indexing for other personas
        documents = self._load_documents_from_directory(docs_path)
        self.logger.info(f"Loaded {len(documents)} documents from {docs_path}")

        if not documents:
            self.logger.warning(f"No documents found in {docs_path}")
            return 0

        # Index with persona metadata
        chunk_count = self.indexer.index_documents(documents, persona=persona_name)
        self.logger.info(f"Indexed {chunk_count} chunks for persona '{persona_name}'")

        return chunk_count

    def list_personas(self) -> list:
        """List all available personas.

        Returns:
            List of persona directory names
        """
        if not self.personas_dir.exists():
            return []

        personas = [d.name for d in self.personas_dir.iterdir() if d.is_dir()]
        self.logger.debug(f"Found {len(personas)} personas: {personas}")
        return sorted(personas)

    def _load_documents_from_directory(self, directory: Path) -> list:
        """Load all supported documents from a directory.

        Supports: .txt, .pdf, .md files

        Args:
            directory: Path to directory containing documents

        Returns:
            List of loaded Document objects
        """
        documents = []

        # Load text files (.txt)
        for txt_file in directory.glob("**/*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                documents.extend(loader.load())
                self.logger.debug(f"Loaded {txt_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load {txt_file}: {e}")

        # Load PDF files
        for pdf_file in directory.glob("**/*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents.extend(loader.load())
                self.logger.debug(f"Loaded {pdf_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load {pdf_file}: {e}")

        # Load markdown files (.md)
        for md_file in directory.glob("**/*.md"):
            try:
                loader = TextLoader(str(md_file), encoding='utf-8')
                documents.extend(loader.load())
                self.logger.debug(f"Loaded {md_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load {md_file}: {e}")

        return documents
