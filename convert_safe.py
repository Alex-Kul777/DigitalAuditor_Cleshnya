#!/usr/bin/env python3
"""Safe conversion with timeout + error handling."""

import os
import sys
import signal
import time
from pathlib import Path

os.environ["LOG_LEVEL"] = "DEBUG-1"
sys.path.insert(0, "/home/kap/projects/DigitalAuditor_Cleshnya")

from tools.document_converter import convert_pdf_to_markdown

def timeout_handler(signum, frame):
    print(f"[⚠ TIMEOUT] Conversion exceeded limit")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(1200)  # 20-min hard timeout

try:
    print("[START] Converting CISA (1232 pages)")
    print(f"[TIME] {time.strftime('%H:%M:%S')}")

    result = convert_pdf_to_markdown(Path("personas/CISA/raw/CISA Review Manual.pdf"))

    print(f"\n[✓ SUCCESS] {result.name}")
    print(f"[SIZE] {result.stat().st_size} bytes ({result.stat().st_size/1024:.0f} KB)")
    print(f"[LINES] {len(result.read_text().splitlines())}")
    print(f"[TIME] {time.strftime('%H:%M:%S')}")

except Exception as e:
    print(f"[✗ ERROR] {e}", file=sys.stderr)
    sys.exit(1)
finally:
    signal.alarm(0)
