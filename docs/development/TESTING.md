# Testing Guide

Comprehensive guide to testing DigitalAuditor Cleshnya.

## Overview

The test suite uses **pytest** with three testing layers:

1. **Unit Tests** (~370): Isolated components with mocks
2. **Smoke Tests** (~45): Import and CLI verification
3. **Integration Tests**: Full workflow with real Ollama (local only)

### Current Coverage

- **Phase 2 Target**: 40% ✅ Achieved
- **Phase 3 Target**: 54% (under development)
- **Coverage Tools**: pytest-cov with Codecov reporting

## Quick Start

### Running Tests

```bash
# All tests (unit + smoke)
make test

# With coverage report
make test-cov

# Specific test file
pytest tests/unit/test_config.py -v

# Specific test class
pytest tests/unit/test_validator.py::TestValidateTaskConfig -v

# Single test
pytest tests/unit/test_validator.py::TestValidateTaskConfig::test_valid_config -v
```

### Test Markers

```bash
# Only unit tests
pytest -m unit

# Only smoke tests
pytest -m smoke

# Exclude slow tests
pytest -m "not slow"
```

## Test Structure

### Directory Layout

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_validator.py
│   ├── test_agents.py
│   └── test_tools.py
├── smoke/                   # Smoke tests
│   └── test_smoke.py
└── integration/             # Integration tests (future)
    └── test_audit_task.py   # Full workflow tests
```

## Core Fixtures

### Provided in conftest.py

```python
# Configuration
@pytest.fixture
def sample_audit_config():
    """Standard audit configuration."""
    return {
        "name": "test_audit",
        "company": "Test Company",
        "audit_type": "it",
    }

# File System
@pytest.fixture
def tmp_task_dir(tmp_path):
    """Temporary task directory with standard structure."""
    task_dir = tmp_path / "test_task"
    task_dir.mkdir()
    (task_dir / "evidence").mkdir()
    (task_dir / "drafts").mkdir()
    (task_dir / "output").mkdir()
    return task_dir

# Environment
@pytest.fixture
def env_testing(monkeypatch):
    """Set up testing environment variables."""
    monkeypatch.setenv("AUDIT_PROFILE", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

# Mocks
@pytest.fixture
def mock_ollama_llm():
    """Mock Ollama LLM instance."""
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value="Test response")
    return mock_llm

@pytest.fixture
def mock_audit_config(monkeypatch):
    """Mock audit configuration with testing profile."""
    # Returns AuditConfig with testing-specific settings
    pass
```

## Writing Unit Tests

### Test Class Structure

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestMyModule:
    """Test MyModule functionality."""
    
    def test_happy_path(self):
        """Test normal operation."""
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_value
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(MyException):
            my_function(invalid_input)
    
    def test_with_mock(self, mock_ollama_llm):
        """Test using a fixture."""
        mock_ollama_llm.invoke.return_value = "Test"
        # Test code here
        assert mock_ollama_llm.invoke.called
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_with_patch():
    """Test using patch decorator."""
    with patch("module.external_function") as mock_func:
        mock_func.return_value = "mocked"
        result = code_under_test()
        assert result == "mocked"
        mock_func.assert_called_once()

@patch("module.OllamaLLM")
def test_with_decorator(mock_ollama_class):
    """Test using patch decorator syntax."""
    mock_instance = MagicMock()
    mock_ollama_class.return_value = mock_instance
    
    # Use mock_instance in test
    assert mock_instance.invoke.called
```

### Testing Exceptions

```python
def test_exception_raised():
    """Test that exception is raised."""
    with pytest.raises(TaskNotFoundError) as exc_info:
        find_task("nonexistent")
    
    assert "TASK_NOT_FOUND" in str(exc_info.value)
    assert exc_info.value.error_code == "TASK_NOT_FOUND"

def test_exception_contains_context():
    """Test exception includes context."""
    with pytest.raises(ValidationError) as exc_info:
        validate_config({})
    
    error = exc_info.value
    assert error.field == "name"
    assert error.expected == "non-empty string"
```

### Testing File I/O

```python
def test_file_operations(tmp_path):
    """Test with temporary file system."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    # Test code
    result = read_and_process(test_file)
    
    # Verify
    assert result == "processed content"
    assert test_file.exists()
```

## Pattern Examples

### Testing Validators

```python
class TestInputValidator:
    """Test InputValidator class."""
    
    def test_valid_config(self):
        """Test validation passes for valid config."""
        config = {
            "name": "test",
            "company": "Test Corp",
            "audit_type": "it",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_config(self):
        """Test validation fails for invalid config."""
        config = {"name": "test"}  # Missing company, audit_type
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any(e.field == "company" for e in result.errors)

    @pytest.mark.parametrize("audit_type", ["it", "security", "compliance"])
    def test_valid_audit_types(self, audit_type):
        """Test all valid audit types."""
        config = {
            "name": "test",
            "company": "Test Corp",
            "audit_type": audit_type,
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True
```

### Testing Agents with Mocked LLM

```python
class TestCisaAuditor:
    """Test CisaAuditor agent."""
    
    def test_execute_with_mocked_llm(self, mock_ollama_llm):
        """Test agent execution with mocked Ollama."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.execute("test task")
                
                # Verify LLM was called
                mock_ollama_llm.invoke.assert_called_once()
                
                # Verify prompt contains system prompt
                called_prompt = mock_ollama_llm.invoke.call_args[0][0]
                assert SYSTEM_PROMPT in called_prompt
                assert "test task" in called_prompt
```

### Testing Data Persistence

```python
def test_evidence_tracker_persistence(tmp_path):
    """Test evidence is persisted to file."""
    task_dir = tmp_path / "test_task"
    task_dir.mkdir()
    (task_dir / "evidence").mkdir()
    
    # Add evidence
    tracker = EvidenceTracker(task_dir)
    tracker.add("source", "content", "High")
    
    # Verify persistence
    evidence_file = task_dir / "evidence" / "evidence_log.json"
    assert evidence_file.exists()
    
    # Verify can reload
    tracker2 = EvidenceTracker(task_dir)
    assert len(tracker2.evidence) == 1
    assert tracker2.evidence[0]["source"] == "source"
```

## Advanced Testing

### Fixtures with Dependencies

```python
@pytest.fixture
def config_with_validator(sample_audit_config, monkeypatch):
    """Fixture that uses another fixture."""
    monkeypatch.setenv("AUDIT_PROFILE", "testing")
    config = sample_audit_config
    result = InputValidator.validate_task_config(config)
    return config, result

def test_with_dependent_fixture(config_with_validator):
    """Test using dependent fixture."""
    config, validation = config_with_validator
    assert validation.is_valid
```

### Parametrized Tests

```python
class TestRiskMatrix:
    """Test risk matrix with parametrization."""
    
    @pytest.mark.parametrize("probability,impact,expected", [
        ("High", "High", "Critical"),
        ("High", "Medium", "High"),
        ("Low", "Low", "Low"),
    ])
    def test_all_combinations(self, probability, impact, expected):
        """Test all risk combinations."""
        result = calculate_risk_level(probability, impact)
        assert result == expected
```

### Test Markers

```python
# Mark test as slow
@pytest.mark.slow
def test_slow_operation():
    # This test takes a while
    pass

# Mark test as integration
@pytest.mark.integration
def test_with_real_ollama():
    # Requires Ollama running
    pass

# Mark test as unit
@pytest.mark.unit
def test_isolated_function():
    # No external dependencies
    pass
```

## CI/CD Integration

### GitHub Actions Testing

Tests run automatically on:
- **Push** to main/master/develop
- **Pull Requests** against main/master/develop

### Coverage Reporting

```bash
# Generate coverage report
pytest --cov=core --cov=agents --cov-report=term-missing

# Generate HTML report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Local Testing Before Push

```bash
# Run all tests locally
make test

# Check coverage
make test-cov

# Run with verbose output
pytest -v --tb=short

# Run specific marker
pytest -m unit -v
```

## Troubleshooting

### Import Errors in Tests

**Problem**: `ModuleNotFoundError: No module named 'core'`

**Solution**: Ensure setup.py is installed:
```bash
pip install -e .
```

### Fixture Not Found

**Problem**: `fixture 'mock_ollama_llm' not found`

**Solution**: Verify fixture is in conftest.py:
```bash
grep -r "def mock_ollama_llm" tests/
```

### Test Hangs

**Problem**: Test never completes

**Solution**: Check for infinite loops or network calls:
```python
# Add timeout
@pytest.mark.timeout(10)  # Timeout after 10 seconds
def test_that_hangs():
    pass
```

### Mocking Not Working

**Problem**: Mock not being called

**Solution**: Patch at the location where it's used:
```python
# ❌ Wrong: patch at definition
with patch("module.OllamaLLM"):
    # This won't work if already imported

# ✅ Correct: patch at usage location
with patch("agents.cisa_auditor.OllamaLLM"):
    auditor = CisaAuditor()
```

## Best Practices

### 1. Test Naming

```python
# ❌ Bad names
def test_1():
    pass

def test_thing():
    pass

# ✅ Good names
def test_valid_config_passes_validation():
    pass

def test_missing_name_field_raises_error():
    pass
```

### 2. Arrange-Act-Assert

```python
def test_example():
    # Arrange: Set up test data
    config = {"name": "test", "company": "Test"}
    
    # Act: Execute code under test
    result = validate(config)
    
    # Assert: Verify results
    assert result.is_valid
```

### 3. One Assertion (Usually)

```python
# ❌ Multiple assertions for different things
def test_config():
    result = validate(config)
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.warnings == []

# ✅ Separate tests
def test_valid_config_passes():
    result = validate(config)
    assert result.is_valid

def test_valid_config_has_no_errors():
    result = validate(config)
    assert len(result.errors) == 0
```

### 4. Mock External Dependencies

```python
# ✅ Good: Mock Ollama
@patch("agents.cisa_auditor.OllamaLLM")
def test_auditor(mock_ollama):
    mock_ollama.return_value.invoke.return_value = "response"
    # Test doesn't need real Ollama running
```

### 5. Use Fixtures for Reusable Setup

```python
# ❌ Repeated setup
def test_1():
    tracker = EvidenceTracker(tmp_task_dir)
    tracker.add("source", "content", "High")
    # Test code

def test_2():
    tracker = EvidenceTracker(tmp_task_dir)
    tracker.add("source", "content", "High")
    # Test code

# ✅ Fixture for reuse
@pytest.fixture
def tracker_with_evidence(tmp_task_dir):
    tracker = EvidenceTracker(tmp_task_dir)
    tracker.add("source", "content", "High")
    return tracker

def test_1(tracker_with_evidence):
    # Test code

def test_2(tracker_with_evidence):
    # Test code
```

## Coverage Goals

### Phase 2 (Current)
- **Target**: 40%
- **Status**: ✅ Achieved
- **Focus**: Core modules (config, logger, validator, exceptions, risk_matrix)

### Phase 3 (In Progress)
- **Target**: 54%
- **Focus**: knowledge/, report_generator/ modules
- **New test files**: test_knowledge.py, test_report_generator.py

## Related Documentation

- [LOGGING_GUIDE.md](LOGGING_GUIDE.md) — Structured logging patterns
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Operational issues
- [CLAUDE.md](../../CLAUDE.md) — Project overview
- [README.md](../../README.md) — Quick start

---

**Last Updated**: 2026-04-20
