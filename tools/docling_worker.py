#!/usr/bin/env python3
"""Docling subprocess worker — converts PDF chunk, writes Markdown to output file.

Called by document_converter.py for each chunk or page.

Usage:
  python docling_worker.py <pdf_path> <start_page> <end_page> <output_file>

Example:
  python docling_worker.py report.pdf 1 50 /tmp/chunk1.md

Exit codes:
  0 = success (output_file written)
  1 = failure (error printed to stderr)

This script runs in isolated process. On completion or timeout, OS reclaims all memory.
"""

import sys
import os
from pathlib import Path

os.environ["LOG_LEVEL"] = "DEBUG-1"

if __name__ == "__main__":
    try:
        if len(sys.argv) != 5:
            raise ValueError("Usage: docling_worker.py <pdf_path> <start> <end> <output>")

        pdf_path = Path(sys.argv[1])
        start_page = int(sys.argv[2])
        end_page = int(sys.argv[3])
        output_file = Path(sys.argv[4])

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(pdf_path), page_range=(start_page, end_page))
        md = result.document.export_to_markdown()

        output_file.write_text(md, encoding="utf-8")
        print(f"OK:{len(md)}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
