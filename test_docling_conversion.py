#!/usr/bin/env python3
"""Test Docling PDF to Markdown conversion with progress bar and max logging."""

import os
import sys
from pathlib import Path

# Set maximum logging before importing anything else
os.environ["LOG_LEVEL"] = "DEBUG-1"

from tqdm import tqdm
from core.logger import setup_logger

logger = setup_logger("docling_test")

def test_docling_conversion():
    """Convert first 20 pages of CISA Review Manual to Markdown."""

    pdf_path = Path("personas/CISA/raw/CISA Review Manual.pdf")
    output_path = Path("personas/CISA/raw/CISA Review Manual_p1_20_test.md")

    logger.info(f"Starting Docling conversion test")
    logger.info(f"Input: {pdf_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Pages: 1-20")

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return False

    try:
        logger.info("Importing docling...")
        from docling.document_converter import DocumentConverter

        logger.info("Initializing DocumentConverter...")
        converter = DocumentConverter()

        logger.info("Starting conversion (page_range=(1, 20))...")
        with tqdm(total=1, desc="Docling conversion", unit="doc") as pbar:
            result = converter.convert(
                str(pdf_path),
                page_range=(1, 20)
            )
            pbar.update(1)

        logger.info("Exporting to Markdown...")
        md_content = result.document.export_to_markdown()

        logger.info(f"Writing {len(md_content)} bytes to {output_path}")
        output_path.write_text(md_content, encoding="utf-8")

        logger.info(f"✓ Conversion complete")
        logger.info(f"  Output file: {output_path}")
        logger.info(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
        logger.info(f"  Lines: {len(md_content.splitlines())}")

        return True

    except ImportError as e:
        logger.error(f"Docling import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Conversion failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_docling_conversion()
    sys.exit(0 if success else 1)
