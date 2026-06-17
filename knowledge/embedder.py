from langchain_community.embeddings import HuggingFaceEmbeddings
from core.config import EMBEDDING_MODEL
from core.logger import setup_logger

logger = setup_logger("embedder")

_embedder_cache = None

def get_embedder():
    """Get cached embedder instance. Loads only once per session."""
    global _embedder_cache

    if _embedder_cache is None:
        logger.info(f"Loading embedder model: {EMBEDDING_MODEL}")
        _embedder_cache = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        logger.debug(f"Embedder model loaded and cached")
    else:
        logger.debug(f"Using cached embedder model: {EMBEDDING_MODEL}")

    return _embedder_cache
