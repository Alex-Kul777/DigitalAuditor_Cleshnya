"""
Configuration management for DigitalAuditor Cleshnya.

Supports multiple profiles (testing, production, development)
with dataclass-based configuration for type safety.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent

# Brink's Modern Internal Auditing configuration
BRINKS_CHUNK_SIZE = 512  # Medium chunk for balance between detail & context
BRINKS_CHAPTERS_INDEX = "knowledge/brinks_chapters.json"


@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM."""

    base_url: str
    model: str
    timeout_seconds: int = 30
    max_retries: int = 3

    def validate(self) -> bool:
        """Validate Ollama configuration."""
        if not self.base_url.startswith("http"):
            return False
        if not self.model:
            return False
        return True


@dataclass
class KnowledgeConfig:
    """Configuration for knowledge base and embeddings."""

    raw_docs_path: Path
    vector_store_path: Path
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 500
    overlap: int = 50

    def validate(self) -> bool:
        """Validate knowledge configuration."""
        return bool(self.embedding_model)


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    log_file: str
    log_level: str
    json_output: bool = False
    json_file: Optional[str] = None

    def validate(self) -> bool:
        """Validate logging configuration."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        return self.log_level.upper() in valid_levels


@dataclass
class AuditConfig:
    """Configuration for audit execution."""

    ollama: OllamaConfig
    knowledge: KnowledgeConfig
    logging: LoggingConfig
    tavily_api_key: str = ""
    profile: str = "development"
    debug: bool = False

    def validate(self) -> bool:
        """Validate all sub-configurations."""
        return (
            self.ollama.validate()
            and self.knowledge.validate()
            and self.logging.validate()
        )


def _get_ollama_config(profile: str) -> OllamaConfig:
    """Get Ollama configuration for the given profile."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "digital-auditor-cisa")
    timeout = int(os.getenv("OLLAMA_TIMEOUT", "30"))
    retries = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))

    # Mock LLM for testing profile
    if profile == "testing":
        return OllamaConfig(
            base_url="http://localhost:11434",
            model="digital-auditor-cisa",  # Will be mocked
            timeout_seconds=5,
            max_retries=1,
        )

    return OllamaConfig(
        base_url=base_url,
        model=model,
        timeout_seconds=timeout,
        max_retries=retries,
    )


def _get_knowledge_config(profile: str) -> KnowledgeConfig:
    """Get knowledge configuration for the given profile."""
    raw_docs = PROJECT_ROOT / "knowledge" / "raw_docs"
    vector_store = PROJECT_ROOT / "chroma_db"

    # Use in-memory embeddings for testing
    if profile == "testing":
        vector_store = PROJECT_ROOT / ".chroma_test_db"

    return KnowledgeConfig(
        raw_docs_path=raw_docs,
        vector_store_path=vector_store,
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        chunk_size=500,
        overlap=50,
    )


def _get_logging_config(profile: str) -> LoggingConfig:
    """Get logging configuration for the given profile."""
    log_file = os.getenv("LOG_FILE", "audit.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    json_output = os.getenv("LOG_JSON", "false").lower() == "true"

    # More verbose logging in development
    if profile == "development":
        log_level = os.getenv("LOG_LEVEL", "DEBUG")
        json_output = True

    # Minimal logging in production
    if profile == "production":
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Silent JSON in testing
    if profile == "testing":
        log_level = "WARNING"
        json_output = False

    json_file = None
    if json_output:
        json_file = str(Path(log_file).parent / "audit.json")

    return LoggingConfig(
        log_file=log_file,
        log_level=log_level,
        json_output=json_output,
        json_file=json_file,
    )


def create_config(profile: Optional[str] = None) -> AuditConfig:
    """
    Create configuration for the given profile.

    Args:
        profile: Configuration profile (testing, production, development)
                 If None, uses AUDIT_PROFILE env var or defaults to development

    Returns:
        AuditConfig instance
    """
    if profile is None:
        profile = os.getenv("AUDIT_PROFILE", "development")

    if profile not in ("testing", "production", "development"):
        raise ValueError(f"Invalid profile: {profile}")

    return AuditConfig(
        ollama=_get_ollama_config(profile),
        knowledge=_get_knowledge_config(profile),
        logging=_get_logging_config(profile),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        profile=profile,
        debug=os.getenv("DEBUG", "false").lower() == "true",
    )


# Default singleton instance (for backward compatibility)
_default_config: Optional[AuditConfig] = None


def get_config(profile: Optional[str] = None) -> AuditConfig:
    """
    Get or create the configuration singleton.

    Args:
        profile: Configuration profile (overrides singleton if provided)

    Returns:
        AuditConfig instance
    """
    global _default_config
    if profile is not None or _default_config is None:
        _default_config = create_config(profile)
    return _default_config


# Legacy module-level exports for backward compatibility
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "digital-auditor-cisa")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "audit.log")

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hybrid")

# GigaChat Configuration
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")
GIGACHAT_MAX_TOKENS = int(os.getenv("GIGACHAT_MAX_TOKENS", "2000"))
GIGACHAT_TIMEOUT = int(os.getenv("GIGACHAT_TIMEOUT", "60"))
GIGACHAT_MAX_RETRIES = int(os.getenv("GIGACHAT_MAX_RETRIES", "3"))

# Claude/Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

KNOWLEDGE_RAW_DOCS = PROJECT_ROOT / "knowledge" / "raw_docs"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
