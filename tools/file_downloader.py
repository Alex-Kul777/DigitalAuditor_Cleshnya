import requests
from pathlib import Path
from urllib.parse import urlparse
from core.logger import setup_logger

logger = setup_logger("downloader")

def download_file(url: str, dest_dir: Path) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    parsed = urlparse(url)
    filename = Path(parsed.path).name or "document.txt"
    file_path = dest_dir / filename
    file_path.write_bytes(response.content)
    logger.info(f"Downloaded: {file_path}")
    return file_path
