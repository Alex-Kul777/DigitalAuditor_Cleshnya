# DigitalAuditor Cleshnya — AI Audit Agent

🇷🇺 [Русская версия](README_RU.md)

## 📋 Overview

AI-powered audit system for IT compliance audits following CISA (Certified Information Systems Auditor) and CIA (Certified Internal Auditor) standards.

**Key Features:**
- RAG on ChromaDB + FAISS for semantic document retrieval
- Multiple LLM support: GigaChat, Claude, OpenAI, Ollama (local)
- Multi-persona audit framework (CisaAuditor, uncle_Robert, uncle_Kahneman)
- DOCX export/import with Track Changes revision cycle
- Evidence traceability with 3-level requirements hierarchy
- User preference learning from revision feedback

## ✨ What's New (Latest Release)

## [2.0.0]

**Major release**: All 5 core milestones (M1-M5) complete + Process Mining logging. Production-ready with 54% coverage, 300+ tests.

### Added

#### M5 — Personalization (6 tasks ✅)
- User preference learning system via Track Changes feedback (term substitutions, min frequency 2)
- PreferencesStore + UserPreferences dataclass with 4 preference categories
- Auto-learning in revision cycle (preference_learner.py)
- Automatic preference application in report generation prompts
- 19 unit tests for ...

## 🚀 Features

Auto-generated from CHANGELOG:


[See CHANGELOG.md for complete list](CHANGELOG.md)

## 📁 Project Structure

```

**core/**
- `__init__/`
- `config.py`
- `exceptions.py`
- `gigachat_client.py`
- `gigachat_validator.py`
- `llm.py`
- `logger.py`
- `logging_utils.py`
- `preferences.py`
- `token_counter.py`

**agents/**
- `__init__/`
- `base.py`
- `cisa_auditor.py`
- `preference_learner.py`
- `prompts.py`
- `reviewer_base.py`
- `revision_agent.py`
- `uncle_kahneman.py`
- `uncle_robert.py`

**knowledge/**
- `__init__/`
- `brinks_indexer.py`
- `embedder.py`
- `evidence_indexer.py`
- `fetcher.py`
- `indexer.py`
- `persona_indexer.py`
- `raw_docs.py`
- `requirements_indexer.py`
- `retriever.py`

**report_generator/**
- `__init__/`
- `assembler.py`
- `ccce_formatter.py`
- `chapters.py`
- `docx.py`
- `orchestrator.py`
- `orchestrator_ms.py`
- `templates.py`

**tools/**
- `__init__/`
- `docling_worker.py`
- `document_converter.py`
- `evidence_tracker.py`
- `file_downloader.py`
- `risk_matrix.py`
- `web_search.py`

**tasks/**
- `__init__/`
- `base_task.py`
- `instances.py`
- `ms_copilot_audit.py`

**presentation/**
- `data.py`
- `generate.py`
- `slides.py`

**process_mining/**
- `__init__/`
- `process_mining_logger.py`
```

## 🧪 Test Coverage

- **Total Tests:** 0+ unit + integration tests
- **Coverage:** 54% (Phase 3 target achieved ✅)
- **Test Files:** tests/unit/, tests/integration/, tests/smoke/

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya
cd DigitalAuditor_Cleshnya

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: digital-auditor-cisa)

# Ensure Ollama is running
# then create and run an audit task
python main.py create --name demo_audit --company DemoCompany --audit-type it
python main.py run --task demo_audit
```

## 🛠️ Installation

**Requirements:** Python 3.10+, Ollama (local)

[See docs/development/TROUBLESHOOTING.md for detailed setup](docs/development/TROUBLESHOOTING.md)

## 🚦 Usage

```bash
# Create audit task
python main.py create --name <task_name> --company <company> --audit-type <type>

# Run audit
python main.py run --task <task_name>

# List tasks
python main.py list-tasks

# Build auditor persona
python main.py build-persona <persona_name>

# Export to DOCX
python main.py export-docx --task <task_name>

# Revise report
python main.py revise --task <task_name> --feedback <feedback_file>

# Add requirements
python main.py add-requirement --level L1 --title "Requirement" --description "..."
```

## 🔧 Configuration

**Environment Variables** (see `.env.example`):
- `OLLAMA_BASE_URL` — Local Ollama endpoint
- `OLLAMA_MODEL` — Model name (default: digital-auditor-cisa)
- `CHROMA_DB_PATH` — Vector store location
- `TAVILY_API_KEY` — Web search API key (optional)
- `LOG_LEVEL` — Logging verbosity (INFO, DEBUG, WARNING, ERROR)

## 🧪 Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_agents.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v
```

## 📚 Documentation

- [Development Guide](docs/development/LOGGING_GUIDE.md) — Logging patterns, pipeline tracing
- [Testing Guide](docs/development/TESTING.md) — Test writing, fixtures, CI/CD
- [Troubleshooting](docs/development/TROUBLESHOOTING.md) — Common issues and solutions
- [ROADMAP](ROADMAP.md) — Milestones M1-M5, completed features
- [CHANGELOG](CHANGELOG.md) — Version history and release notes
- [Architecture](docs/GAP_ANALYSIS.md) — System design decisions

## 📄 License

MIT License — See LICENSE file

## 📧 Contact

- **Author:** Alexey K.
- **Telegram:** [@auditor2it](https://t.me/auditor2it)

---

**Status:** Production-ready (v2.0.0) | All 5 core milestones (M1-M5) complete ✅
