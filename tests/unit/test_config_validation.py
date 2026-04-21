"""Test configuration validation for audit tasks."""
import pytest
from core.validator import InputValidator
from core.exceptions import ValidationError


class TestAuditTypeValidation:
    """Test audit_type configuration validation."""

    def test_valid_audit_types(self):
        """Verify all valid audit types are accepted."""
        valid_types = {"it", "security", "compliance", "operational", "financial"}
        for audit_type in valid_types:
            config = {
                "name": "test_audit",
                "company": "Test Co",
                "audit_type": audit_type,
            }
            result = InputValidator.validate_task_config(config)
            assert result.is_valid, f"audit_type '{audit_type}' should be valid"

    def test_invalid_audit_type_forensic(self):
        """Verify 'forensic' audit type is rejected."""
        config = {
            "name": "test_audit",
            "company": "Test Co",
            "audit_type": "forensic",
        }
        result = InputValidator.validate_task_config(config)
        assert not result.is_valid, "Should reject invalid audit_type"
        assert any("forensic" in e.message for e in result.errors)

    def test_invalid_audit_type_custom(self):
        """Verify custom invalid audit types are rejected."""
        invalid_types = ["testing", "fraud", "management", "risk"]
        for audit_type in invalid_types:
            config = {
                "name": "test_audit",
                "company": "Test Co",
                "audit_type": audit_type,
            }
            result = InputValidator.validate_task_config(config)
            assert not result.is_valid, f"Should reject invalid audit_type: {audit_type}"

    def test_missing_audit_type(self):
        """Verify missing audit_type is caught."""
        config = {"name": "test_audit", "company": "Test Co"}
        result = InputValidator.validate_task_config(config)
        assert not result.is_valid, "Should require audit_type field"


class TestTaskConfigRequiredFields:
    """Test required fields validation."""

    def test_missing_required_fields(self):
        """Verify all required fields are checked."""
        required_fields = {"name", "company", "audit_type"}

        for missing_field in required_fields:
            config = {
                "name": "test_audit",
                "company": "Test Co",
                "audit_type": "it",
            }
            del config[missing_field]

            result = InputValidator.validate_task_config(config)
            assert not result.is_valid, f"Should require '{missing_field}' field"

    def test_valid_minimal_config(self):
        """Verify minimal valid config passes."""
        config = {
            "name": "test_audit",
            "company": "Test Co",
            "audit_type": "it",
        }
        result = InputValidator.validate_task_config(config)
        assert result.is_valid, "Minimal valid config should pass"
