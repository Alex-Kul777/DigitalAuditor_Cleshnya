from core.logger import setup_logger

logger = setup_logger("web_search")

def search_urls(query: str, max_results: int = 3) -> list:
    logger.info(f"Searching: {query}")
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [r['href'] for r in results]
    except ImportError:
        logger.warning("duckduckgo-search not installed")
        return []
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []
