"""
Custom exception classes for DigitalAuditor Cleshnya.

All custom exceptions inherit from AuditError for easy catching
and provide error codes for programmatic handling.
"""


class AuditError(Exception):
    """Base exception for all audit-related errors."""

    def __init__(self, message: str, error_code: str = "UNKNOWN", details: dict = None):
        """
        Initialize AuditError with message and error code.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for handling
            details: Additional context dictionary
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.error_code}: {self.message})"


class TaskNotFoundError(AuditError):
    """Raised when an audit task is not found."""

    def __init__(self, task_name: str):
        super().__init__(
            f"Audit task '{task_name}' not found",
            error_code="TASK_NOT_FOUND",
            details={"task_name": task_name},
        )


class OllamaUnavailableError(AuditError):
    """Raised when Ollama LLM is unavailable or unreachable."""

    def __init__(self, base_url: str, original_error: Exception = None):
        msg = f"Ollama is unavailable at {base_url}"
        if original_error:
            msg += f": {str(original_error)}"
        super().__init__(
            msg,
            error_code="OLLAMA_UNAVAILABLE",
            details={"base_url": base_url},
        )
        self.original_error = original_error


class ValidationError(AuditError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str = None,
        expected: str = None,
        actual: str = None,
    ):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "expected": expected,
                "actual": actual,
            },
        )
        self.field = field
        self.expected = expected
        self.actual = actual


class KnowledgeIndexError(AuditError):
    """Raised when knowledge base indexing fails."""

    def __init__(self, message: str, document_id: str = None):
        super().__init__(
            message,
            error_code="KNOWLEDGE_INDEX_ERROR",
            details={"document_id": document_id},
        )
        self.document_id = document_id


class ConfigurationError(AuditError):
    """Raised when configuration is invalid or missing required fields."""

    def __init__(self, message: str, missing_fields: list = None):
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            details={"missing_fields": missing_fields},
        )
        self.missing_fields = missing_fields or []


class DocumentFetchError(AuditError):
    """Raised when document fetching fails."""

    def __init__(self, source: str, original_error: Exception = None):
        msg = f"Failed to fetch documents from source: {source}"
        if original_error:
            msg += f": {str(original_error)}"
        super().__init__(
            msg,
            error_code="DOCUMENT_FETCH_ERROR",
            details={"source": source},
        )
        self.source = source
        self.original_error = original_error


class ReportGenerationError(AuditError):
    """Raised when report generation fails."""

    def __init__(self, message: str, section: str = None):
        super().__init__(
            message,
            error_code="REPORT_GENERATION_ERROR",
            details={"section": section},
        )
        self.section = section


class ProcessMiningError(AuditError):
    """Raised when process mining logging fails."""

    def __init__(self, message: str, stage: str = None):
        super().__init__(
            message,
            error_code="PROCESS_MINING_ERROR",
            details={"stage": stage},
        )
        self.stage = stage
