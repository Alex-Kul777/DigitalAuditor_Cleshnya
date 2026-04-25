# Changelog

All notable changes to DigitalAuditor Cleshnya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (Auto-generated entries from merged PRs will appear here)

### Changed
- (Auto-generated entries from merged PRs will appear here)

### Fixed
- (Auto-generated entries from merged PRs will appear here)

---

## [2.0.0] - 2026-04-25

**Major release**: All 5 core milestones (M1-M5) complete + Process Mining logging. Production-ready with 54% coverage, 300+ tests.

### Added

#### M5 — Personalization (6 tasks ✅)
- User preference learning system via Track Changes feedback (term substitutions, min frequency 2)
- PreferencesStore + UserPreferences dataclass with 4 preference categories
- Auto-learning in revision cycle (preference_learner.py)
- Automatic preference application in report generation prompts
- 19 unit tests for preference system

#### M4 — DOCX Export & Revision Cycle (6 tasks ✅)
- DOCX backend adapter layer supporting 3 libraries (PythonDocx, DocxEditor, DocxRevisions)
- Markdown to DOCX export with Track Changes comments
- DOCX import with feedback extraction and comment separation
- Version management with manifest tracking (versions/ directory)
- LLM-guided revision loop with revision_agent.py
- 9 integration tests for full DOCX export/import/revise cycle
- CLI commands: export-docx, revise, import-feedback

#### M_Evidence — Evidence Traceability & Requirements Hierarchy (8 tasks ✅)
- Metadata-based document filtering (doc_type, req_level, page_number, task_name)
- Requirements management: L1 (Regulatory), L2 (Audit Standard), L3 (Local) levels
- Evidence indexing with SHA-256 incremental per-task tracking
- Source awareness in audit findings with automatic citations
- CLI commands: create (with source download), add-requirement
- Evidence collection sync before report generation
- 41 integration tests for evidence collection and requirements

#### M_Robert — uncle_Robert Primary Auditor (8 tasks ✅)
- Alternative primary auditor based on IIA Professional Practices Framework + Brink's Modern Internal Auditing
- CCCE format (Condition/Criteria/Cause/Effect) for findings
- Draft→Final two-stage audit pipeline
- Brink's chapter-based RAG retrieval with 26 indexed chapters
- Activatable via --auditor uncle_robert CLI flag
- 27 unit tests (14 UncleRobertAgent + 13 BrinksIndexer)

#### M3 — Reviewer Integration (4 tasks ✅)
- Reviewer hook in report orchestrator (post-audit analysis)
- CLI --reviewer flag for run/create commands
- Soft validation warnings for unknown reviewers
- 7 integration tests for reviewer hook

#### M2 — Reviewer Agent: UncleKahneman (5 tasks ✅)
- S1/S2 cognitive bias detection algorithm (System 1 fast / System 2 slow deliberate)
- LLMFactory with mode support (cheap/deep) for cost-efficient multi-pass review
- UncleKahneman persona leveraging Kahneman's cognitive psychology principles
- 18 unit tests for two-pass review logic

#### M1 — Persona Infrastructure (7 tasks ✅)
- Metadata-based persona filtering in ChromaDB (exclude_personas, filter by persona)
- Multi-persona framework without knowledge contamination
- Persona scaffolding and corpus management
- CLI facade: build-persona command with corpus ingestion
- Persona registry for discovery and listing
- Orchestrator integration with persona awareness
- 40 unit tests for persona filtering

#### Process Mining Logging System
- ProcessMiningLogger for capturing system processes and audit actions
- CSV, JSON, plain text export formats
- Process logs directory (process_logs/)
- 33 unit + integration tests

### Changed

- `report_generator/orchestrator.py` — Reviewer hook integration, persona filtering, evidence awareness
- `core/llm.py` — LLMFactory with mode-based model selection (cheap/deep)
- `knowledge/retriever.py` — Metadata-based filtering (persona, requirements level, task scope)
- `core/config.py` — Brinks chapter constants and configuration expansion
- `main.py` — New CLI commands: build-persona, add-requirement, export-docx, revise, import-feedback; --auditor and --reviewer flags

### Fixed

- Task isolation: Audit tasks no longer share vector store contamination
- Evidence citation accuracy: All findings now link to source documents
- Persona knowledge segregation: Reviewer corpora no longer bleed into audit findings
- DOCX revision cycle: Proper Track Changes handling across import/export

---

## [1.1.0] - 2026-04-20 (Phase 3 Complete)

---

## [1.1.0] - 2026-04-20 (Phase 3 Complete)

### Added

#### Phase 3: Polish & Documentation
- **Development Guides**:
  - `docs/development/LOGGING_GUIDE.md` (400+ lines): Advanced logging patterns, LogContext, PipelineTimer, process mining
  - `docs/development/TESTING.md` (350+ lines): Test writing guide, fixtures, mocking patterns, CI/CD integration
  - `docs/development/TROUBLESHOOTING.md` (350+ lines): Solutions for Ollama, ChromaDB, config, logging, performance issues

- **Extended Test Coverage**:
  - `tests/unit/test_knowledge.py`: 170+ tests for DocumentFetcher, VectorIndexer, Retriever
  - `tests/unit/test_report_generator.py`: 130+ tests for ReportOrchestrator, report structure, findings aggregation
  - Knowledge module: Multilingual support, edge cases, document persistence
  - Report generation: Multiple formats (Markdown, JSON), evidence linking, risk categorization

- **Total Coverage**: 54% achieved (Phase 3 target)
  - Phase 1: Core modules (config, logger, validator, exceptions) - 250+ tests
  - Phase 2: Agents, tools, infrastructure - 165+ tests
  - Phase 3: Knowledge, report generation - 300+ tests
  - **Total**: 715+ unit tests + 45 smoke tests = 760+ total tests

### Improved

- Documentation structure: Added development guides for operational support
- Test coverage: Extended to cover knowledge base and report generation
- Process mining: Comprehensive logging guide for audit trail analysis

---

## [1.0.0] - 2026-04-20

### Added

#### Phase 1: Foundation
- **Package Infrastructure**
  - `setup.py` for pip installation (`pip install -e .`)
  - Entry point for `digital-auditor` CLI command
  - Development extras for testing (`pytest`, `pytest-cov`, `pytest-mock`)

- **Test Infrastructure**
  - `pytest.ini` with test markers (unit, integration, smoke)
  - `.coveragerc` for coverage measurement
  - `conftest.py` with 5 core fixtures (audit config, task dir, Ollama mock, ChromaDB mock)
  - 250+ unit and smoke tests across 8 test files

- **Core Libraries**
  - `core/exceptions.py`: 8 custom exception classes with error codes
  - `core/validator.py`: InputValidator with ValidationResult dataclass
  - `core/logging_utils.py`: ContextualFormatter, JSONFormatter, DualLogHandler, LogContext
  - `core/logger.py`: Refactored for dual text + JSON logging

- **Development Tools**
  - `Makefile`: 8 targets (install, test, test-cov, test-unit, clean, lint, format)
  - `.env.example`: Documented configuration template

#### Phase 2: Quality
- **Configuration Management**
  - Dataclass-based config (`OllamaConfig`, `KnowledgeConfig`, `LoggingConfig`, `AuditConfig`)
  - Profile support: `testing`, `production`, `development`
  - Factory function `create_config()` with singleton `get_config()`
  - Profile-specific behavior (mock Ollama for testing, DEBUG logging for development)

- **Extended Test Coverage**
  - `tests/unit/test_agents.py`: 90 tests for agent classes and LLM interaction
  - `tests/unit/test_tools.py`: 75 tests for evidence tracking and tools
  - Mock audit config fixture for testing profile
  - Enhanced mock_ollama_llm with langchain compatibility

- **CI/CD Pipeline**
  - `.github/workflows/tests.yml`: GitHub Actions workflow
  - Python 3.10, 3.11, 3.12 matrix testing
  - Coverage reporting to Codecov
  - Separate unit and integration test jobs
  - Optional security scanning with Bandit

- **Documentation**
  - Comprehensive `README.md` (500+ lines)
    - Quick start guide
    - Architecture overview
    - Configuration reference
    - API documentation
    - Troubleshooting section
  - `CHANGELOG.md` (this file) with structured version history

### Changed

- **core/config.py**: Refactored from simple module-level variables to dataclass-based configuration
  - Maintains backward compatibility with legacy exports
  - Adds profile-aware initialization
  - Improved type safety with dataclasses

- **core/logger.py**: Simplified to use `DualLogHandler` for consistent setup
  - Support for optional JSON output
  - Automatic logs directory creation
  - Prevention of handler duplication

- **tasks/base_task.py**: Enhanced error handling and validation
  - Pre-execution configuration validation
  - Comprehensive error logging with context
  - Wrapping of unexpected exceptions in AuditError

- **main.py**: Added pre-flight checks and error handling
  - Ollama connectivity verification before task execution
  - User-friendly error messages for common failures
  - Proper exit codes (0 for success, 1 for errors)

### Fixed

- Incorrect logger instance duplication prevention
- Configuration override behavior with environment variables
- Exception messages now include error codes for programmatic handling

### Security

- Input validation for all audit configuration parameters
- File path validation for evidence documents
- Ollama URL format verification
- Timeout handling for external service calls

### Testing

- **Total Tests**: 415+
  - Unit tests: 370+
  - Smoke tests: 45+
  - Coverage: 40% (Phase 2 target)

- **Test Categories**:
  - Configuration and environment management
  - Exception handling and validation
  - Logging and structured output
  - Agent execution with mocked LLM
  - Evidence tracking and persistence
  - Risk matrix calculations
  - Import and CLI verification

- **Fixtures**:
  - `sample_audit_config`: Standard audit configuration
  - `tmp_task_dir`: Temporary task directory with structure
  - `env_testing`: Testing environment variables
  - `mock_ollama_llm`: Mocked Ollama instance
  - `mock_audit_config`: Testing-profile configuration
  - `mock_chroma_db`: Mocked ChromaDB
  - `mock_embedder`: Mocked embeddings

### Deployment

- Backward compatibility maintained with legacy configuration exports
- Profile-based configuration enables environment-specific behavior
- CI/CD pipeline enables automated testing and deployment

## Known Limitations

- Integration tests require Ollama running locally (not in CI/CD)
- Coverage at 40% (Phase 3 target: 54%)
- No web UI (planned for v1.1+)
- Limited to single-node execution (no distributed audits)

## Future Roadmap

### v1.1 (Planned)
- Extended knowledge base with custom audit profiles
- Advanced report templates with custom sections
- Real-time progress tracking
- Audit comparison and trending

### v2.0 (Planned)
- Web UI for audit management
- Real-time collaboration features
- Custom audit profile builder
- Integration with ITSM platforms

### v2.1+ (Future)
- Distributed audit execution
- Machine learning-based risk prediction
- Automated compliance mapping
- Advanced visualization dashboards

## Contributors

- Technical Architecture: Claude Sonnet 4.6 (2026-04-20)
- Implementation: Claude Haiku 4.5 (Phase 1-2, 2026-04-20)

---

**For questions or issues, please visit: https://github.com/your-org/DigitalAuditor_Cleshnya**
