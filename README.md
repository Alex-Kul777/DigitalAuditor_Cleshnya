# DigitalAuditor Cleshnya

**AI-powered compliance audit system following CISA (Certified Information Systems Auditor) and CIA (Certified Internal Auditor) standards.**

[![Tests](https://github.com/your-org/DigitalAuditor_Cleshnya/actions/workflows/tests.yml/badge.svg)](https://github.com/your-org/DigitalAuditor_Cleshnya/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DigitalAuditor Cleshnya is an intelligent audit system that leverages Large Language Models (Ollama) to conduct comprehensive IT security and compliance audits. It supports document analysis, evidence tracking, risk assessment, and professional report generation.

## Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Ollama**: Running locally (download from [ollama.ai](https://ollama.ai))
- **Model**: `digital-auditor-cisa` installed in Ollama

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/DigitalAuditor_Cleshnya.git
cd DigitalAuditor_Cleshnya

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and set:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: digital-auditor-cisa)
# - TAVILY_API_KEY (for web search features)
```

### First Audit

```bash
# Create an audit task
python main.py create \
  --name "security_audit_2026" \
  --company "ACME Corp" \
  --audit-type it \
  --sources "network_documentation" "security_logs"

# Run the audit
python main.py run --task security_audit_2026

# Check results
ls tasks/instances/security_audit_2026/output/
```

## Core Features

### 🤖 AI-Powered Analysis
- Uses Ollama LLM for professional audit analysis
- CISA/CIA-aligned system prompts in Russian
- Supports document retrieval and evidence linking

### 📊 Evidence Management
- Centralized evidence tracking with timestamps
- Source attribution and relevance scoring
- JSON-based persistence for integration

### 🎯 Risk Assessment
- Probability × Impact risk matrix
- Five-level risk classification (Critical, High, Medium, Low)
- Audit-specific risk aggregation

### 📄 Report Generation
- Professional audit report orchestration
- Chapter-based structure for clarity
- Findings with evidence references

### 🔍 Knowledge Base
- Vector embeddings for semantic search (ChromaDB)
- Multilingual support (Russian, English, etc.)
- Automatic document chunking and indexing

## Architecture

### Directory Structure

```
DigitalAuditor_Cleshnya/
├── core/                    # Core infrastructure
│   ├── config.py           # Configuration management (dataclass-based)
│   ├── logger.py           # Structured logging setup
│   ├── logging_utils.py    # Advanced logging utilities
│   ├── exceptions.py       # Custom exception hierarchy
│   └── validator.py        # Input validation framework
│
├── agents/                  # Audit agents
│   ├── base.py             # BaseAgent abstract class
│   └── cisa_auditor.py     # CISA/CIA auditor agent
│
├── tasks/                   # Task orchestration
│   └── base_task.py        # AuditTask executor
│
├── knowledge/              # Knowledge management
│   ├── fetcher.py          # Document source fetching
│   ├── indexer.py          # Vector embedding & indexing
│   └── retriever.py        # Semantic document search
│
├── tools/                   # Utility tools
│   ├── evidence_tracker.py # Evidence collection
│   ├── risk_matrix.py      # Risk assessment
│   ├── web_search.py       # Web search integration
│   └── file_downloader.py  # Document downloading
│
├── report_generator/       # Report generation
│   ├── orchestrator.py     # Report assembly
│   └── chapters/           # Report sections
│
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── unit/               # Unit tests (250+)
│   └── smoke/              # Import/CLI smoke tests
│
├── main.py                 # CLI entry point
├── setup.py                # Package configuration
├── pytest.ini              # Test configuration
├── Makefile                # Development targets
└── .env.example            # Environment template
```

### Data Flow

```
CLI (main.py)
    ↓
Task Creation & Validation
    ↓
Document Fetching (knowledge.fetcher)
    ↓
Vector Indexing (knowledge.indexer → ChromaDB)
    ↓
Audit Execution (agents.cisa_auditor + tasks.base_task)
    ├→ Evidence Collection (tools.evidence_tracker)
    ├→ Risk Assessment (tools.risk_matrix)
    └→ Document Retrieval (knowledge.retriever)
    ↓
Report Generation (report_generator.orchestrator)
    ↓
Output (tasks/instances/{task_name}/output/)
```

## Configuration

### Profiles

Configuration varies by profile (set via `AUDIT_PROFILE` environment variable):

| Profile | Ollama | Logging | Vector Store | Use Case |
|---------|--------|---------|--------------|----------|
| **testing** | Mock | WARNING | In-memory | Unit tests, CI/CD |
| **development** | Real | DEBUG + JSON | Persistent | Local development |
| **production** | Real | INFO | Persistent | Deployed audits |

### Environment Variables

```bash
# Profile & LLM
AUDIT_PROFILE=development          # testing, production, development
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=digital-auditor-cisa
OLLAMA_TIMEOUT=30
OLLAMA_MAX_RETRIES=3

# External APIs
TAVILY_API_KEY=sk-...             # Web search API key

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=audit.log
LOG_JSON=false                    # Enable JSON output for process mining

# Debugging
DEBUG=false                       # Enable debug mode
```

## Development

### Running Tests

```bash
# All tests (unit + smoke)
make test

# With coverage report
make test-cov

# Unit tests only
make test-unit

# Smoke tests (imports, CLI)
make test-smoke

# Integration tests (requires Ollama)
make test-integration
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint
```

### Installation Options

```bash
# Production
pip install -e .

# Development (with test dependencies)
pip install -e ".[dev]"
```

## API Reference

### CLI Commands

```bash
# Create audit task
python main.py create --name <task_name> --company <company> --audit-type <type> [--sources <s1> <s2> ...]

# Run audit task
python main.py run --task <task_name>

# List tasks
python main.py list-tasks

# Microsoft Copilot Chat audit (specialized)
python main.py audit-ms
```

### Core Classes

#### AuditTask

```python
from tasks.base_task import AuditTask
from pathlib import Path

task = AuditTask(Path("tasks/instances/my_audit"))
task.execute()  # Runs full audit pipeline
```

#### CISAAuditor

```python
from agents.cisa_auditor import CISAAuditor

auditor = CISAAuditor()
findings = auditor.execute("Проверить ИТ-безопасность")
section = auditor.generate_section("Опишите политики контроля доступа")
```

#### InputValidator

```python
from core.validator import InputValidator

config = {
    "name": "audit_x",
    "company": "ACME",
    "audit_type": "it"
}
result = InputValidator.validate_task_config(config)
if result.is_valid:
    print("Config is valid")
else:
    for error in result.errors:
        print(f"[{error.error_code}] {error.message}")
```

#### EvidenceTracker

```python
from tools.evidence_tracker import EvidenceTracker
from pathlib import Path

tracker = EvidenceTracker(Path("tasks/instances/my_audit"))
tracker.add("network_scan", "10 open ports detected", "High")
tracker.add("log_review", "Failed login attempts: 50", "Medium")
```

## Testing Strategy

### Test Layers

1. **Unit Tests** (250+): Individual components with mocks
   - Core modules: config, logger, validator, exceptions
   - Agents and tools: CISA auditor, evidence tracking, risk matrix
   - Run in CI/CD without external dependencies

2. **Smoke Tests** (45+): Import and CLI verification
   - Module imports (14 tests)
   - CLI commands (6 tests)
   - File structure (8 tests)
   - Basic functionality (8 tests)

3. **Integration Tests**: Full workflow with real Ollama
   - Run locally only: `make test-integration`
   - Requires Ollama running on localhost:11434

### Coverage

- Current: 40% (Phase 2 target)
- Phase 3 goal: 54%
- Focus areas: core, agents, tasks, tools

## Troubleshooting

### Ollama is Unavailable

```
Error: Ollama is unavailable at http://localhost:11434

Solution:
1. Install Ollama from ollama.ai
2. Start Ollama: ollama serve
3. Pull model: ollama pull digital-auditor-cisa
4. Verify: curl http://localhost:11434/api/tags
```

### ChromaDB Errors

```
Error: Failed to initialize vector store

Solution:
1. Clear vector store: rm -rf chroma_db/
2. Rebuild index: python scripts/rebuild_index.py
3. Check permissions: ls -la chroma_db/
```

### Import Errors

```
Error: ModuleNotFoundError: No module named 'core'

Solution:
1. Install in development mode: pip install -e .
2. Verify venv is activated: which python
3. Check Python path: python -c "import sys; print(sys.path)"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/xyz`
3. Write tests for new functionality
4. Run tests: `make test`
5. Commit with detailed messages
6. Push and create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Project Status

- **v1.0** (current): Core audit functionality, 250+ tests, comprehensive logging
- **v1.1** (planned): Extended knowledge base, advanced reporting
- **v2.0** (planned): Web UI, real-time collaboration, custom audit profiles

## Resources

- [CISA Standards](https://www.isaca.org/certifications/cisa)
- [CIA Standards](https://www.iia.org/certifications/certified-internal-auditor)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report a bug](https://github.com/your-org/DigitalAuditor_Cleshnya/issues)
- Documentation: [See docs/](docs/)
- Email: support@your-org.com

---

**Made with ❤️ for compliance professionals**
