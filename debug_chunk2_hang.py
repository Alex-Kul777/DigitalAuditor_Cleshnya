#!/usr/bin/env python3
"""Debug script for Chunk 2 (pages 100-200) conversion hang.

Comprehensive logging of each Docling conversion stage:
- Memory usage tracking
- Timing for each operation
- PDF processing progress
- Exception handling with full traceback
"""

import os
import sys
import time
import psutil
from pathlib import Path
from datetime import datetime

os.environ["LOG_LEVEL"] = "DEBUG-2"
sys.path.insert(0, "/home/kap/projects/DigitalAuditor_Cleshnya")

from core.logger import setup_logger

logger = setup_logger("chunk2_debug")

# Track process memory
process = psutil.Process(os.getpid())

def log_memory():
    """Log current memory usage."""
    mem = process.memory_info()
    percent = process.memory_percent()
    return f"{mem.rss / 1024 / 1024:.1f} MB ({percent:.1f}%)"

def log_timing(start_time, label):
    """Log elapsed time since start."""
    elapsed = time.time() - start_time
    return f"{elapsed:.2f}s"

# Start main pipeline
logger.info("="*70)
logger.info("CHUNK 2 HANG DEBUG - Pages 101-200")
logger.info("="*70)
logger.info(f"Start time: {datetime.now().isoformat()}")
logger.info(f"Initial memory: {log_memory()}")

pdf_path = Path("personas/CISA/raw/CISA Review Manual.pdf")
page_range = (101, 200)

if not pdf_path.exists():
    logger.error(f"PDF not found: {pdf_path}")
    sys.exit(1)

logger.info(f"Input: {pdf_path.name}")
logger.info(f"Pages: {page_range[0]}-{page_range[1]}")
logger.info(f"PDF size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")

# === STAGE 1: Import Docling ===
logger.info("")
logger.info("[STAGE 1] Importing Docling...")
logger.debug(f"  Memory before import: {log_memory()}")

stage1_start = time.time()
try:
    from docling.document_converter import DocumentConverter
    logger.info(f"  ✓ Import successful ({log_timing(stage1_start, 'import')})")
    logger.debug(f"  Memory after import: {log_memory()}")
except Exception as e:
    logger.error(f"  ✗ Import failed: {e}", exc_info=True)
    sys.exit(1)

# === STAGE 2: Create DocumentConverter ===
logger.info("")
logger.info("[STAGE 2] Creating DocumentConverter instance...")
logger.debug(f"  Memory before creation: {log_memory()}")

stage2_start = time.time()
try:
    converter = DocumentConverter()
    logger.info(f"  ✓ Converter created ({log_timing(stage2_start, 'creation')})")
    logger.debug(f"  Memory after creation: {log_memory()}")
    logger.debug(f"  Converter type: {type(converter).__name__}")
except Exception as e:
    logger.error(f"  ✗ Converter creation failed: {e}", exc_info=True)
    sys.exit(1)

# === STAGE 3: Start PDF conversion ===
logger.info("")
logger.info(f"[STAGE 3] Converting PDF (pages {page_range[0]}-{page_range[1]})...")
logger.debug(f"  Memory before conversion: {log_memory()}")
logger.debug(f"  Page range tuple: {page_range}")

stage3_start = time.time()
checkpoint_time = time.time()

try:
    logger.debug("  Calling converter.convert()...")
    result = converter.convert(str(pdf_path), page_range=page_range)

    stage3_elapsed = time.time() - stage3_start
    logger.info(f"  ✓ Conversion successful ({stage3_elapsed:.2f}s)")
    logger.debug(f"  Memory after conversion: {log_memory()}")

    # === STAGE 4: Check result ===
    logger.info("")
    logger.info("[STAGE 4] Analyzing conversion result...")

    if hasattr(result, 'document'):
        doc = result.document
        logger.debug(f"  Document type: {type(doc).__name__}")

        if hasattr(doc, 'pages'):
            num_pages = len(doc.pages)
            logger.info(f"  ✓ Document has {num_pages} pages")
            logger.debug(f"  Pages list length: {num_pages}")

            if num_pages != (page_range[1] - page_range[0] + 1):
                logger.warning(f"  Page count mismatch: expected {page_range[1] - page_range[0] + 1}, got {num_pages}")
        else:
            logger.warning("  Document has no 'pages' attribute")
    else:
        logger.warning("  Result has no 'document' attribute")

    # === STAGE 5: Export to Markdown ===
    logger.info("")
    logger.info("[STAGE 5] Exporting document to Markdown...")
    logger.debug(f"  Memory before export: {log_memory()}")

    stage5_start = time.time()
    md_content = result.document.export_to_markdown()
    stage5_elapsed = time.time() - stage5_start

    logger.info(f"  ✓ Export successful ({stage5_elapsed:.2f}s)")
    logger.info(f"  Markdown size: {len(md_content)} bytes ({len(md_content) / 1024:.1f} KB)")
    logger.info(f"  Line count: {len(md_content.splitlines())}")
    logger.debug(f"  Memory after export: {log_memory()}")

    # === SUMMARY ===
    logger.info("")
    logger.info("="*70)
    logger.info("[SUCCESS] Chunk 2 conversion completed")
    logger.info("="*70)

    total_time = time.time() - stage1_start
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Final memory: {log_memory()}")
    logger.info(f"End time: {datetime.now().isoformat()}")

    # Timeline
    logger.info("")
    logger.info("Timing breakdown:")
    logger.info(f"  Stage 1 (Import):     {log_timing(stage1_start, 'import')}")
    logger.info(f"  Stage 2 (Create):     {log_timing(stage2_start, 'create')}")
    logger.info(f"  Stage 3 (Convert):    {stage3_elapsed:.2f}s")
    logger.info(f"  Stage 5 (Export):     {stage5_elapsed:.2f}s")

except Exception as e:
    elapsed = time.time() - stage3_start
    logger.error(f"  ✗ Conversion failed after {elapsed:.2f}s")
    logger.error(f"  Exception: {e}", exc_info=True)
    logger.error(f"  Memory at failure: {log_memory()}")

    import traceback
    logger.error("")
    logger.error("Full traceback:")
    for line in traceback.format_exc().splitlines():
        logger.error(f"  {line}")

    sys.exit(1)
