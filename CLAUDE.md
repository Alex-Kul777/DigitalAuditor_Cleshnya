# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DigitalAuditor Cleshnya** is an AI-powered audit system designed for compliance audits following CISA (Certified Information Systems Auditor) and CIA (Certified Internal Auditor) standards. It's built around a modular agent-based architecture with LLM integration, knowledge management, and report generation capabilities.

The system supports conducting various types of audits (IT audits, security assessments) and generates comprehensive audit reports with findings, risk assessments, and compliance recommendations.

## Setup & Dependencies

**Environment Setup:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: digital-auditor-cisa)
# - TAVILY_API_KEY (web search API key)
```

**Dependencies Overview:**
- **LLM**: Ollama (via `langchain-ollama`) - must be running locally
- **Vector Store**: ChromaDB with sentence-transformers embeddings
- **Task Management**: Click CLI framework
- **Knowledge Retrieval**: LangChain with RAG capabilities
- **Web Search**: Tavily and DuckDuckGo APIs
- **Document Processing**: BeautifulSoup4, pypdf, python-docx, markdown, pandas
- **Testing**: pytest

## Common Commands

```bash
# Create a new audit task
python main.py create --name <task_name> --company <company_name> --audit-type <type> [--sources <source1> <source2>]

# Run an existing audit task
python main.py run --task <task_name>

# List all audit tasks
python main.py list-tasks

# Run Microsoft Copilot Chat audit (specialized flow)
python main.py audit-ms

# Run tests
pytest
pytest tests/test_retriever.py  # Single test file
pytest -v                       # Verbose output

# Run a specific test
pytest tests/test_retriever.py::test_retriever_init

# Rebuild vector index
python scripts/rebuild_index.py

# Generate documentation
python scripts/generate_docs.py
```

## Architecture & Key Components

### Core Module (`core/`)
- **config.py**: Centralized configuration from environment variables and .env file
  - `OLLAMA_BASE_URL`, `OLLAMA_MODEL`: LLM endpoint configuration
  - `CHROMA_DB_PATH`: Vector store location
  - `EMBEDDING_MODEL`: Sentence transformer for embeddings
  - Project root paths and logging configuration

- **llm.py**: LLM instantiation helper
  - `get_llm(temperature)`: Factory function returns OllamaLLM instance with configured parameters

- **logger.py**: Unified logging setup
  - Logs to both file (`audit.log`) and console
  - Respects LOG_LEVEL environment variable

### Agents Module (`agents/`)
- **base.py**: Abstract `BaseAgent` class
  - All agents inherit from BaseAgent
  - Provides standardized access to LLM and logger

- **cisa_auditor.py**: Main CISA/CIA auditor agent
  - System prompt enforces professional Russian language output
  - `execute(task)`: Main audit execution method
  - `generate_section(prompt)`: Generates specific report sections

### Tasks Module (`tasks/`)
- **base_task.py**: Core `AuditTask` orchestrator
  - Loads task configuration from `tasks/instances/{task_name}/config.yaml`
  - Coordinates document fetching, indexing, and report generation
  - Task directories structure:
    - `evidence/`: Audit evidence files
    - `drafts/`: Working drafts
    - `output/`: Generated reports and outputs
    - `config.yaml`: Task configuration (name, company, audit_type, sources)

### Knowledge Module (`knowledge/`)
Implements RAG (Retrieval-Augmented Generation) pattern:

- **fetcher.py**: `DocumentFetcher` class
  - Retrieves documents from configured sources
  - Supports multiple document types

- **indexer.py**: `VectorIndexer` class
  - Embeds documents using sentence-transformers
  - Stores embeddings in Chroma DB vector store
  - Maps document IDs to registry

- **retriever.py**: `Retriever` class
  - Query documents from indexed knowledge base
  - Returns relevant documents for LLM context

- **embedder.py**: Embedding model management
  - Uses `paraphrase-multilingual-MiniLM-L12-v2` for multilingual support

- **raw_docs/**: Knowledge source documents (populated during indexing)
- **vector_store/**: Chroma DB storage location

### Report Generator Module (`report_generator/`)
- **orchestrator.py**: `ReportOrchestrator` class
  - Main entry point for report generation
  - Coordinates sections, assembles findings into structured output

- **orchestrator_ms.py**: Specialized orchestrator for Microsoft Copilot audits
  - Custom logic for MS-specific audit flows

- **assembler.py**: Report assembly utilities
  - Combines sections into final report format

- **chapters/**: Report chapter templates
- **templates/**: Jinja2 or similar templates for report sections

### Tools Module (`tools/`)
- **risk_matrix.py**: Risk assessment matrix (likelihood × impact)
- **evidence_tracker.py**: Tracks audit evidence collection and linking
- **web_search.py**: Web search utilities (Tavily/DuckDuckGo)
- **file_downloader.py**: Document download and caching

### Process Mining (`process_mining/`)
- **process_mining_logger.py**: Captures and logs system processes
- Logs stored in `process_logs/` (CSV, JSON, plain text formats)

### Presentation Module (`presentation/`)
- Generates audit presentation slides
- Audience-specific versions: executive, practitioner, technical
- Metrics/data driven visualizations

## Development Notes

### Task Execution Flow
1. User creates task via CLI: `python main.py create --name audit_x --company CompanyName`
2. Task directory structure created under `tasks/instances/{task_name}/`
3. User runs task: `python main.py run --task audit_x`
4. AuditTask loads config, fetches documents, builds vector index
5. Report orchestrator generates findings and output
6. Results available in task's `output/` directory

### Vector Index Management
The knowledge base uses ChromaDB for semantic search:
- First run: documents fetched, embedded, and indexed
- Subsequent runs: can query existing index
- Rebuild index if documents change: `python scripts/rebuild_index.py`
- Index stored in `chroma_db/` directory (in .gitignore)

### Audit Types
- Default: `"it"` (IT audit)
- Others defined by audit scope (stored in task config)
- Different orchestrators can be plugged in per audit type

### Configuration Hierarchy
1. `.env` file (local, gitignored)
2. `config.py` defaults
3. Task-specific `config.yaml` overrides
4. CLI arguments (via Click)

### Logging
All components use Python's `logging` module through `setup_logger(name)`:
- Logs to `audit.log` file in project root
- Also outputs to console
- Format: `timestamp - logger_name - level - message`
- Change verbosity via `LOG_LEVEL` env var (INFO, DEBUG, WARNING, ERROR)

## Testing

Tests are in `tests/` directory using pytest:
- `test_retriever.py`: Knowledge retrieval functionality
- `test_risk_matrix.py`: Risk assessment logic
- `fixtures/`: Test data and mock data

Run tests before committing changes. Tests should import from project root (not relative imports).

## Important Notes

- **Ollama Requirement**: The system expects Ollama running locally with a custom model `digital-auditor-cisa`. Ensure Ollama is started before running audits.
- **API Keys**: Tavily API key needed for web search features. Set in `.env` file.
- **Language**: System prompts use Russian for audit output. Responses follow official-business Russian style.
- **Vector Store**: ChromaDB is stateful. Index updates may require rebuild if documents change significantly.
- **Task Isolation**: Each audit task is independent with its own directory. Outputs and evidence don't interfere.
