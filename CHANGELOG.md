# Changelog

All notable changes to DigitalAuditor Cleshnya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
