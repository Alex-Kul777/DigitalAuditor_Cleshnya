"""
Input validation for DigitalAuditor Cleshnya.

Provides comprehensive validation with detailed error reporting
following the rag_GigaChat pattern.
"""
import socket
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import requests

from core.exceptions import (
    ValidationError,
    OllamaUnavailableError,
    ConfigurationError,
)


@dataclass
class ValidationErrorDetail:
    """Details about a validation error."""

    field: str
    error_code: str
    message: str
    expected: str = ""
    actual: str = ""


@dataclass
class ValidationResult:
    """Result of validation with detailed error reporting."""

    is_valid: bool
    errors: List[ValidationErrorDetail] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(
        self,
        field: str,
        error_code: str,
        message: str,
        expected: str = "",
        actual: str = "",
    ):
        """Add a validation error."""
        self.errors.append(
            ValidationErrorDetail(
                field=field,
                error_code=error_code,
                message=message,
                expected=expected,
                actual=actual,
            )
        )
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)

    def __str__(self):
        msg = f"ValidationResult(valid={self.is_valid})"
        if self.errors:
            msg += f"\nErrors ({len(self.errors)}):"
            for err in self.errors:
                msg += f"\n  - [{err.error_code}] {err.field}: {err.message}"
        if self.warnings:
            msg += f"\nWarnings ({len(self.warnings)}):"
            for warn in self.warnings:
                msg += f"\n  - {warn}"
        return msg


class InputValidator:
    """Validator for audit inputs and configuration."""

    VALID_AUDIT_TYPES = {"it", "security", "compliance", "operational", "financial"}

    VALID_LEVELS = {"Low", "Medium", "High", "Critical"}

    @staticmethod
    def validate_task_config(config: Dict[str, Any]) -> ValidationResult:
        """
        Validate audit task configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(is_valid=True)

        required_fields = {"name", "company", "audit_type"}
        for field in required_fields:
            if field not in config or not config[field]:
                result.add_error(
                    field=field,
                    error_code="MISSING",
                    message=f"Required field '{field}' is missing",
                    expected="non-empty string",
                    actual="missing",
                )

        # Validate audit_type
        if "audit_type" in config:
            audit_type = config.get("audit_type", "").lower()
            if audit_type not in InputValidator.VALID_AUDIT_TYPES:
                result.add_error(
                    field="audit_type",
                    error_code="UNSUPPORTED_FORMAT",
                    message=f"Audit type '{audit_type}' is not supported",
                    expected="|".join(InputValidator.VALID_AUDIT_TYPES),
                    actual=audit_type,
                )

        # Validate name length
        if "name" in config:
            name = config["name"]
            if len(str(name)) < 3:
                result.add_warning("Task name is quite short (< 3 chars)")
            if len(str(name)) > 100:
                result.add_error(
                    field="name",
                    error_code="TOO_SHORT",
                    message="Task name is too long (> 100 chars)",
                    expected="<= 100 chars",
                    actual=str(len(name)),
                )

        # Validate company name
        if "company" in config:
            company = config["company"]
            if len(str(company)) < 2:
                result.add_warning("Company name is quite short (< 2 chars)")

        # Validate sources (optional)
        if "sources" in config:
            sources = config["sources"]
            if sources and not isinstance(sources, (list, tuple)):
                result.add_error(
                    field="sources",
                    error_code="UNSUPPORTED_FORMAT",
                    message="Sources must be a list",
                    expected="list",
                    actual=type(sources).__name__,
                )

        return result

    @staticmethod
    def validate_evidence_file(file_path: Path) -> ValidationResult:
        """
        Validate evidence file.

        Args:
            file_path: Path to evidence file

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(is_valid=True)

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            result.add_error(
                field="file_path",
                error_code="NOT_FOUND",
                message=f"Evidence file not found: {file_path}",
                expected="existing file",
                actual="not found",
            )
            return result

        if not file_path.is_file():
            result.add_error(
                field="file_path",
                error_code="UNSUPPORTED_FORMAT",
                message=f"Path is not a file: {file_path}",
                expected="regular file",
                actual="directory or special file",
            )
            return result

        file_size = file_path.stat().st_size
        if file_size == 0:
            result.add_warning(f"Evidence file is empty: {file_path}")

        # Check file extension
        valid_extensions = {
            ".pdf",
            ".txt",
            ".docx",
            ".xlsx",
            ".csv",
            ".json",
            ".md",
        }
        if file_path.suffix.lower() not in valid_extensions:
            result.add_warning(
                f"Evidence file has unusual extension: {file_path.suffix}"
            )

        return result

    @staticmethod
    def check_ollama_connection(base_url: str, timeout: int = 5) -> ValidationResult:
        """
        Check if Ollama is accessible.

        Args:
            base_url: Ollama base URL
            timeout: Request timeout in seconds

        Returns:
            ValidationResult with connection status
        """
        result = ValidationResult(is_valid=True)

        try:
            # Parse URL
            if not base_url.startswith("http"):
                result.add_error(
                    field="base_url",
                    error_code="UNSUPPORTED_FORMAT",
                    message=f"Invalid URL format: {base_url}",
                    expected="http:// or https://",
                    actual=base_url,
                )
                return result

            # Try to reach Ollama
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=timeout,
            )

            if response.status_code != 200:
                result.add_error(
                    field="ollama_connection",
                    error_code="OLLAMA_UNAVAILABLE",
                    message=f"Ollama returned status {response.status_code}",
                    expected="200 OK",
                    actual=str(response.status_code),
                )

        except requests.exceptions.ConnectionError as e:
            result.add_error(
                field="ollama_connection",
                error_code="OLLAMA_UNAVAILABLE",
                message=f"Cannot connect to Ollama at {base_url}",
                actual=str(e),
            )
        except requests.exceptions.Timeout:
            result.add_error(
                field="ollama_connection",
                error_code="OLLAMA_UNAVAILABLE",
                message=f"Ollama request timed out (>{timeout}s)",
                actual="timeout",
            )
        except Exception as e:
            result.add_error(
                field="ollama_connection",
                error_code="OLLAMA_UNAVAILABLE",
                message=f"Unexpected error checking Ollama: {str(e)}",
                actual=type(e).__name__,
            )

        return result

    @staticmethod
    def validate_risk_levels(probability: str, impact: str) -> ValidationResult:
        """
        Validate risk level inputs.

        Args:
            probability: Probability level (Low, Medium, High, Critical)
            impact: Impact level (Low, Medium, High, Critical)

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)

        # Risk matrix only uses Low/Medium/High
        valid_levels = {"Low", "Medium", "High"}

        if probability not in valid_levels:
            result.add_error(
                field="probability",
                error_code="UNSUPPORTED_FORMAT",
                message=f"Invalid probability level: {probability}",
                expected="|".join(valid_levels),
                actual=probability,
            )

        if impact not in valid_levels:
            result.add_error(
                field="impact",
                error_code="UNSUPPORTED_FORMAT",
                message=f"Invalid impact level: {impact}",
                expected="|".join(valid_levels),
                actual=impact,
            )

        return result
