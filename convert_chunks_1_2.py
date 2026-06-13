#!/usr/bin/env python3
"""Convert Chunks 1-2 (pages 1-200) with detailed logging and timeout.

Pages 1-100 → Chunk 1
Pages 101-200 → Chunk 2

Timeout per chunk: 3 min (180s)
Fallback: per-page if timeout triggers
Monitor: memory, timing, page counts
"""

import os
import sys
import time
import psutil
import gc
from pathlib import Path
from datetime import datetime
from threading import Thread

os.environ["LOG_LEVEL"] = "DEBUG-1"
sys.path.insert(0, "/home/kap/projects/DigitalAuditor_Cleshnya")

from core.logger import setup_logger

logger = setup_logger("chunks_1_2")
process = psutil.Process(os.getpid())

def log_memory():
    mem = process.memory_info()
    percent = process.memory_percent()
    return f"{mem.rss / 1024 / 1024:.1f} MB ({percent:.1f}%)"

def convert_chunk(chunk_num, start_page, end_page, pdf_path):
    """Convert single chunk with timeout + fallback."""
    chunk_start = time.time()
    timeout_sec = 180
    result = None
    exception = None
    md_content = None

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"CHUNK {chunk_num}: Pages {start_page}-{end_page}")
    logger.info("=" * 70)
    logger.info(f"Start: {datetime.now().isoformat()}")
    logger.info(f"Memory: {log_memory()}")
    logger.info(f"Timeout: {timeout_sec}s")

    # === Stage 1: Import (once per script) ===
    if chunk_num == 1:
        logger.info("")
        logger.info("[STAGE 1] Importing Docling...")
        stage1_start = time.time()
        try:
            from docling.document_converter import DocumentConverter
            logger.info(f"  ✓ Import OK ({time.time() - stage1_start:.2f}s)")
        except Exception as e:
            logger.error(f"  ✗ Import failed: {e}", exc_info=True)
            return None

    # === Stage 2: Create converter ===
    logger.info("")
    logger.info(f"[STAGE 2] Creating DocumentConverter...")
    stage2_start = time.time()
    try:
        converter = DocumentConverter()
        logger.info(f"  ✓ Converter created ({time.time() - stage2_start:.2f}s)")
    except Exception as e:
        logger.error(f"  ✗ Failed: {e}", exc_info=True)
        return None

    # === Stage 3: Full chunk conversion with timeout ===
    logger.info("")
    logger.info(f"[STAGE 3] Converting (timeout: {timeout_sec}s)...")
    logger.debug(f"  Memory before: {log_memory()}")

    stage3_start = time.time()

    def convert():
        nonlocal result, exception
        try:
            logger.debug(f"  Calling converter.convert() page_range=({start_page}, {end_page})...")
            result = converter.convert(str(pdf_path), page_range=(start_page, end_page))
            logger.debug(f"  ✓ Conversion returned ({len(result.document.pages)} pages)")
        except Exception as e:
            exception = e
            logger.error(f"  ✗ Conversion failed: {e}", exc_info=True)

    conv_thread = Thread(target=convert, daemon=False)
    conv_thread.start()
    conv_thread.join(timeout=timeout_sec)

    if conv_thread.is_alive():
        # Timeout
        elapsed = time.time() - stage3_start
        logger.warning(f"  ⚠ TIMEOUT after {elapsed:.1f}s - per-page fallback")

        logger.info("")
        logger.info(f"[STAGE 3B] Per-page fallback...")
        md_parts = []
        failed = []

        for idx, page in enumerate(range(start_page, end_page + 1), 1):
            try:
                res = converter.convert(str(pdf_path), page_range=(page, page))
                md = res.document.export_to_markdown()
                md_parts.append(md)
                logger.info(f"  Page {page} [{idx}/{end_page - start_page + 1}] ✓")
            except Exception as e:
                logger.error(f"  Page {page} [{idx}/{end_page - start_page + 1}] ✗ {e}")
                failed.append(page)

        if md_parts:
            md_content = "\n\n---\n\n".join(md_parts)
            logger.info(f"  Merged {len(md_parts)} pages, {len(failed)} failed")

    elif exception:
        logger.error(f"  ✗ Exception during conversion")
        return None

    elif result:
        elapsed = time.time() - stage3_start
        logger.info(f"  ✓ Conversion OK ({elapsed:.1f}s)")
        logger.debug(f"  Memory after: {log_memory()}")

        # === Stage 4: Export ===
        logger.info("")
        logger.info(f"[STAGE 4] Exporting to Markdown...")
        export_start = time.time()
        md_content = result.document.export_to_markdown()
        export_elapsed = time.time() - export_start
        logger.info(f"  ✓ Export OK ({export_elapsed:.2f}s)")

    # === Save output ===
    if md_content:
        output_path = pdf_path.parent / f"{pdf_path.stem}_p{start_page}_{end_page}.md"
        output_path.write_text(md_content, encoding="utf-8")

        logger.info(f"  Output: {output_path.name}")
        logger.info(f"  Size: {len(md_content) / 1024:.1f} KB ({len(md_content.splitlines())} lines)")

        # === Summary ===
        total_chunk_time = time.time() - chunk_start
        logger.info("")
        logger.info(f"Chunk {chunk_num} time: {total_chunk_time:.1f}s")
        logger.info(f"Final memory: {log_memory()}")
        logger.info(f"End: {datetime.now().isoformat()}")

        # Clean up converter
        del converter
        gc.collect()
        logger.debug(f"Converter deleted, memory: {log_memory()}")

        return output_path

    return None

# === MAIN ===
pdf_path = Path("personas/CISA/raw/CISA Review Manual.pdf")

if not pdf_path.exists():
    logger.error(f"PDF not found: {pdf_path}")
    sys.exit(1)

logger.info("")
logger.info("*" * 70)
logger.info("CONVERT CHUNKS 1-2 (Pages 1-200) with Timeout + Fallback")
logger.info("*" * 70)
logger.info(f"PDF: {pdf_path.name} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
logger.info(f"Start: {datetime.now().isoformat()}")

script_start = time.time()

# Chunk 1: Pages 1-100
chunk1_file = convert_chunk(1, 1, 100, pdf_path)

# Chunk 2: Pages 101-200
chunk2_file = convert_chunk(2, 101, 200, pdf_path)

# === FINAL SUMMARY ===
logger.info("")
logger.info("*" * 70)
logger.info("CONVERSION SUMMARY")
logger.info("*" * 70)

total_time = time.time() - script_start
logger.info(f"Total time: {total_time:.1f}s")
logger.info(f"Final memory: {log_memory()}")
logger.info(f"End: {datetime.now().isoformat()}")

if chunk1_file:
    logger.info(f"✓ Chunk 1: {chunk1_file.name}")
else:
    logger.error("✗ Chunk 1: Failed")

if chunk2_file:
    logger.info(f"✓ Chunk 2: {chunk2_file.name}")
else:
    logger.error("✗ Chunk 2: Failed")

if chunk1_file and chunk2_file:
    logger.info("")
    logger.info("Both chunks converted successfully!")
else:
    sys.exit(1)
