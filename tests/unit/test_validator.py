"""
Unit tests for core.validator module.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.validator import (
    InputValidator,
    ValidationResult,
    ValidationErrorDetail,
)
from core.exceptions import ValidationError


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_init_valid(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_add_error(self):
        """Test adding an error to ValidationResult."""
        result = ValidationResult(is_valid=True)
        result.add_error("name", "MISSING", "Name is required")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].error_code == "MISSING"

    def test_validation_result_add_warning(self):
        """Test adding a warning to ValidationResult."""
        result = ValidationResult(is_valid=True)
        result.add_warning("This is a warning")
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == "This is a warning"

    def test_validation_result_str(self):
        """Test string representation of ValidationResult."""
        result = ValidationResult(is_valid=False)
        result.add_error("field1", "CODE1", "Error message")
        result.add_warning("Warning message")
        str_repr = str(result)
        assert "valid=False" in str_repr
        assert "CODE1" in str_repr
        assert "Warning message" in str_repr


class TestValidateTaskConfig:
    """Test InputValidator.validate_task_config()."""

    def test_valid_config(self):
        """Test validation of a valid config."""
        config = {
            "name": "test_audit",
            "company": "Test Corp",
            "audit_type": "it",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_name(self):
        """Test validation fails when name is missing."""
        config = {"company": "Test Corp", "audit_type": "it"}
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        assert any(e.field == "name" for e in result.errors)

    def test_missing_company(self):
        """Test validation fails when company is missing."""
        config = {"name": "test_audit", "audit_type": "it"}
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        assert any(e.field == "company" for e in result.errors)

    def test_missing_audit_type(self):
        """Test validation fails when audit_type is missing."""
        config = {"name": "test_audit", "company": "Test Corp"}
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        assert any(e.field == "audit_type" for e in result.errors)

    def test_invalid_audit_type(self):
        """Test validation fails for unsupported audit_type."""
        config = {
            "name": "test_audit",
            "company": "Test Corp",
            "audit_type": "invalid",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        error = next((e for e in result.errors if e.field == "audit_type"), None)
        assert error is not None
        assert error.error_code == "UNSUPPORTED_FORMAT"

    def test_valid_audit_types(self):
        """Test all valid audit types pass validation."""
        for audit_type in InputValidator.VALID_AUDIT_TYPES:
            config = {
                "name": "test_audit",
                "company": "Test Corp",
                "audit_type": audit_type,
            }
            result = InputValidator.validate_task_config(config)
            assert result.is_valid is True, f"Failed for audit_type={audit_type}"

    def test_name_too_long(self):
        """Test validation fails when name exceeds max length."""
        config = {
            "name": "x" * 101,
            "company": "Test Corp",
            "audit_type": "it",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        error = next((e for e in result.errors if e.field == "name"), None)
        assert error is not None
        assert error.error_code == "TOO_SHORT"

    def test_name_too_short_warning(self):
        """Test warning when name is very short."""
        config = {
            "name": "ab",
            "company": "Test Corp",
            "audit_type": "it",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True
        assert any("short" in w.lower() for w in result.warnings)

    def test_invalid_sources_type(self):
        """Test validation fails when sources is not a list."""
        config = {
            "name": "test_audit",
            "company": "Test Corp",
            "audit_type": "it",
            "sources": "not_a_list",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is False
        error = next((e for e in result.errors if e.field == "sources"), None)
        assert error is not None

    def test_config_with_sources(self):
        """Test config with valid sources list."""
        config = {
            "name": "test_audit",
            "company": "Test Corp",
            "audit_type": "it",
            "sources": ["source1", "source2"],
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True


class TestValidateEvidenceFile:
    """Test InputValidator.validate_evidence_file()."""

    def test_file_not_found(self):
        """Test validation fails when file doesn't exist."""
        result = InputValidator.validate_evidence_file(Path("/nonexistent/file.pdf"))
        assert result.is_valid is False
        error = next((e for e in result.errors if e.error_code == "NOT_FOUND"), None)
        assert error is not None

    def test_file_exists(self, tmp_path):
        """Test validation passes for existing file."""
        test_file = tmp_path / "evidence.pdf"
        test_file.write_text("test content")
        result = InputValidator.validate_evidence_file(test_file)
        assert result.is_valid is True

    def test_file_is_directory(self, tmp_path):
        """Test validation fails when path is a directory."""
        result = InputValidator.validate_evidence_file(tmp_path)
        assert result.is_valid is False

    def test_empty_file_warning(self, tmp_path):
        """Test warning for empty file."""
        test_file = tmp_path / "empty.pdf"
        test_file.write_text("")
        result = InputValidator.validate_evidence_file(test_file)
        assert result.is_valid is True
        assert any("empty" in w.lower() for w in result.warnings)

    def test_unusual_extension_warning(self, tmp_path):
        """Test warning for unusual file extension."""
        test_file = tmp_path / "evidence.xyz"
        test_file.write_text("test")
        result = InputValidator.validate_evidence_file(test_file)
        assert result.is_valid is True
        assert any("unusual" in w.lower() for w in result.warnings)

    def test_valid_extensions(self, tmp_path):
        """Test all valid file extensions."""
        valid_exts = [".pdf", ".txt", ".docx", ".xlsx", ".csv", ".json", ".md"]
        for ext in valid_exts:
            test_file = tmp_path / f"evidence{ext}"
            test_file.write_text("test")
            result = InputValidator.validate_evidence_file(test_file)
            assert result.is_valid is True, f"Failed for extension {ext}"


class TestCheckOllamaConnection:
    """Test InputValidator.check_ollama_connection()."""

    def test_invalid_url_format(self):
        """Test validation fails for invalid URL format."""
        result = InputValidator.check_ollama_connection("not_a_url")
        assert result.is_valid is False
        error = next((e for e in result.errors if "URL" in e.message), None)
        assert error is not None

    @patch("requests.get")
    def test_successful_connection(self, mock_get):
        """Test successful Ollama connection."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = InputValidator.check_ollama_connection("http://localhost:11434")
        assert result.is_valid is True

    @patch("requests.get")
    def test_connection_refused(self, mock_get):
        """Test when Ollama refuses connection."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = InputValidator.check_ollama_connection("http://localhost:11434")
        assert result.is_valid is False
        assert any(e.error_code == "OLLAMA_UNAVAILABLE" for e in result.errors)

    @patch("requests.get")
    def test_connection_timeout(self, mock_get):
        """Test when Ollama request times out."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        result = InputValidator.check_ollama_connection("http://localhost:11434", timeout=1)
        assert result.is_valid is False
        assert any("timeout" in str(e.message).lower() for e in result.errors)

    @patch("requests.get")
    def test_non_200_status(self, mock_get):
        """Test when Ollama returns non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = InputValidator.check_ollama_connection("http://localhost:11434")
        assert result.is_valid is False


class TestValidateRiskLevels:
    """Test InputValidator.validate_risk_levels()."""

    def test_valid_risk_levels(self):
        """Test valid risk level combinations."""
        valid_levels = ["Low", "Medium", "High"]
        for prob in valid_levels:
            for impact in valid_levels:
                result = InputValidator.validate_risk_levels(prob, impact)
                assert result.is_valid is True

    def test_invalid_probability(self):
        """Test validation fails for invalid probability."""
        result = InputValidator.validate_risk_levels("Invalid", "High")
        assert result.is_valid is False
        error = next((e for e in result.errors if e.field == "probability"), None)
        assert error is not None

    def test_invalid_impact(self):
        """Test validation fails for invalid impact."""
        result = InputValidator.validate_risk_levels("High", "Invalid")
        assert result.is_valid is False
        error = next((e for e in result.errors if e.field == "impact"), None)
        assert error is not None

    def test_critical_not_allowed(self):
        """Test that Critical level is not allowed in risk levels."""
        result = InputValidator.validate_risk_levels("Critical", "High")
        assert result.is_valid is False


@pytest.mark.unit
class TestInputValidatorMarker:
    """Test InputValidator with unit marker."""

    def test_validator_methods_exist(self):
        """Test that all expected validator methods exist."""
        assert hasattr(InputValidator, "validate_task_config")
        assert hasattr(InputValidator, "validate_evidence_file")
        assert hasattr(InputValidator, "check_ollama_connection")
        assert hasattr(InputValidator, "validate_risk_levels")
