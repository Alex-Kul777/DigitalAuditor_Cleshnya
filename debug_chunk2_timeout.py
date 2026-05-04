#!/usr/bin/env python3
"""Debug Chunk 2 hang with timeout + per-page fallback.

Converts pages 101-200:
- First: try full chunk (101-200) with timeout
- If timeout: fall back to per-page conversion (101, 102, 103, ...)
- Log each page success/failure
- Merge single-page outputs at end
"""

import os
import sys
import time
import psutil
import signal
from pathlib import Path
from datetime import datetime
from threading import Thread
from queue import Queue

os.environ["LOG_LEVEL"] = "DEBUG-1"
sys.path.insert(0, "/home/kap/projects/DigitalAuditor_Cleshnya")

from core.logger import setup_logger

logger = setup_logger("chunk2_timeout")
process = psutil.Process(os.getpid())

def log_memory():
    mem = process.memory_info()
    percent = process.memory_percent()
    return f"{mem.rss / 1024 / 1024:.1f} MB ({percent:.1f}%)"

# === CONFIG ===
CHUNK_START, CHUNK_END = 101, 200
TIMEOUT_SECONDS = 180  # 3 min timeout for full chunk
PDF_PATH = Path("personas/CISA/raw/CISA Review Manual.pdf")
CHUNKS_DIR = Path("personas/CISA/raw/chunks")
CHUNKS_DIR.mkdir(exist_ok=True)

logger.info("=" * 70)
logger.info(f"CHUNK 2 TIMEOUT DEBUG - Pages {CHUNK_START}-{CHUNK_END}")
logger.info("=" * 70)
logger.info(f"Start: {datetime.now().isoformat()}")
logger.info(f"Memory: {log_memory()}")
logger.info(f"PDF: {PDF_PATH.name} ({PDF_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
logger.info(f"Timeout: {TIMEOUT_SECONDS}s | Fallback: per-page")

# === STAGE 1: Try full chunk ===
logger.info("")
logger.info("[STAGE 1] Importing Docling...")
stage1_start = time.time()
try:
    from docling.document_converter import DocumentConverter
    logger.info(f"  ✓ Import OK ({time.time() - stage1_start:.2f}s)")
except Exception as e:
    logger.error(f"  ✗ Import failed: {e}", exc_info=True)
    sys.exit(1)

logger.info("[STAGE 2] Creating converter...")
stage2_start = time.time()
try:
    converter = DocumentConverter()
    logger.info(f"  ✓ Converter OK ({time.time() - stage2_start:.2f}s)")
except Exception as e:
    logger.error(f"  ✗ Failed: {e}", exc_info=True)
    sys.exit(1)

# === STAGE 3: Full chunk with timeout ===
logger.info("")
logger.info(f"[STAGE 3] Converting pages {CHUNK_START}-{CHUNK_END} (timeout: {TIMEOUT_SECONDS}s)...")
logger.debug(f"  Memory before: {log_memory()}")

stage3_start = time.time()
result = None
exception = None
conversion_done = False

def convert_chunk():
    global result, exception, conversion_done
    try:
        logger.debug(f"  Calling converter.convert() with page_range=({CHUNK_START}, {CHUNK_END})...")
        stage_start = time.time()
        result = converter.convert(
            str(PDF_PATH),
            page_range=(CHUNK_START, CHUNK_END)
        )
        conversion_done = True
        elapsed = time.time() - stage_start
        logger.debug(f"  ✓ Conversion returned in {elapsed:.1f}s (pages: {len(result.document.pages)})")
    except Exception as e:
        exception = e
        logger.error(f"  ✗ Conversion failed: {e}", exc_info=True)

# Run conversion in thread so we can timeout
conv_thread = Thread(target=convert_chunk, daemon=False)
conv_thread.start()
conv_thread.join(timeout=TIMEOUT_SECONDS)

if conv_thread.is_alive():
    # Timeout! Fall back to per-page
    elapsed = time.time() - stage3_start
    logger.warning(f"  ⚠ TIMEOUT after {elapsed:.1f}s (limit: {TIMEOUT_SECONDS}s) - switching to per-page fallback")
    logger.info("")
    logger.info("[STAGE 3B] Per-page conversion fallback (one page per conversion)...")

    # === STAGE 3B: Per-page fallback ===
    per_page_start = time.time()
    md_parts = []
    failed_pages = []

    for idx, page_num in enumerate(range(CHUNK_START, CHUNK_END + 1), 1):
        page_start = time.time()
        progress = f"{idx}/{CHUNK_END - CHUNK_START + 1}"

        try:
            res = converter.convert(str(PDF_PATH), page_range=(page_num, page_num))
            md = res.document.export_to_markdown()
            md_parts.append(md)
            elapsed_page = time.time() - page_start
            logger.info(f"  Page {page_num} [{progress}] ✓ {elapsed_page:.2f}s ({len(md)} bytes)")

        except Exception as e:
            elapsed_page = time.time() - page_start
            logger.error(f"  Page {page_num} [{progress}] ✗ {elapsed_page:.2f}s: {e}")
            failed_pages.append(page_num)

    # Merge per-page results
    if md_parts:
        full_md = "\n\n---\n\n".join(md_parts)
        output_path = PDF_PATH.parent / f"{PDF_PATH.stem}_p{CHUNK_START}_{CHUNK_END}_fallback.md"
        output_path.write_text(full_md, encoding="utf-8")

        logger.info("")
        logger.info(f"[STAGE 4] Fallback merge complete")
        logger.info(f"  ✓ Output: {output_path.name}")
        logger.info(f"  Pages merged: {CHUNK_END - CHUNK_START + 1 - len(failed_pages)}")
        logger.info(f"  Pages failed: {len(failed_pages)} {failed_pages if failed_pages else ''}")
        logger.info(f"  Markdown size: {len(full_md) / 1024:.1f} KB")
        logger.info(f"  Fallback time: {time.time() - per_page_start:.1f}s")

elif exception:
    # Exception during full chunk
    logger.error(f"  ✗ Exception: {exception}")
    sys.exit(1)

elif result:
    # Success! Full chunk completed
    elapsed = time.time() - stage3_start
    logger.info(f"  ✓ Conversion OK ({elapsed:.1f}s)")
    logger.debug(f"  Memory after: {log_memory()}")
    logger.debug(f"  Document pages: {len(result.document.pages)}")

    # === STAGE 4: Export ===
    logger.info("")
    logger.info("[STAGE 4] Exporting to Markdown...")
    export_start = time.time()
    md_content = result.document.export_to_markdown()
    export_elapsed = time.time() - export_start

    output_path = PDF_PATH.parent / f"{PDF_PATH.stem}_p{CHUNK_START}_{CHUNK_END}.md"
    output_path.write_text(md_content, encoding="utf-8")

    logger.info(f"  ✓ Export OK ({export_elapsed:.2f}s)")
    logger.info(f"  Output: {output_path.name}")
    logger.info(f"  Size: {len(md_content) / 1024:.1f} KB ({len(md_content.splitlines())} lines)")

# === SUMMARY ===
logger.info("")
logger.info("=" * 70)
total = time.time() - stage1_start
logger.info(f"Total time: {total:.1f}s")
logger.info(f"Final memory: {log_memory()}")
logger.info(f"End: {datetime.now().isoformat()}")
logger.info("=" * 70)
