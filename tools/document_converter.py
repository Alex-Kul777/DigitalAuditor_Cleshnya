#!/usr/bin/env python3
"""PDF translation and Markdown conversion tool.

Translates PDFs via pdf2zh (GigaChat backend) and converts to Markdown via Docling.
Both operations are independent: use --translate, --markdown, or both flags.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click
from pypdf import PdfReader, PdfWriter

from core.logger import setup_logger

logger = setup_logger("document_converter")


def _check_deps(need_pdf2zh: bool = False, need_docling: bool = False) -> None:
    """Verify required dependencies are installed.

    Raises SystemExit if missing.
    """
    missing = []

    if need_pdf2zh and shutil.which("pdf2zh") is None:
        missing.append("pdf2zh")

    if need_docling:
        try:
            import docling  # noqa: F401
        except ImportError:
            missing.append("docling")

    if missing:
        msg = f"Missing dependencies: {', '.join(missing)}\nInstall: pip install {' '.join(missing)}"
        logger.error(msg)
        raise SystemExit(msg)


def _get_page_count(pdf_path: Path) -> int:
    """Get total page count from PDF."""
    return len(PdfReader(str(pdf_path)).pages)


def _merge_pdfs(pdf_files: list[Path], output_path: Path) -> None:
    """Merge multiple PDFs into one."""
    writer = PdfWriter()
    for pdf_file in pdf_files:
        writer.append(str(pdf_file))
    with open(output_path, "wb") as fh:
        writer.write(fh)


def translate_pdf(input_path: Path, lang: str = "ru", chunk_size: int | None = None) -> Path:
    """Translate PDF using pdf2zh + Google Translate.

    Args:
        input_path: Path to input PDF
        lang: Target language code (default: 'ru' for Russian)

    Returns:
        Path to translated PDF (stem_<lang>.pdf in same directory)

    Raises:
        SystemExit: If pdf2zh not installed or translation fails
    """
    _check_deps(need_pdf2zh=True)

    input_path = Path(input_path)
    if not input_path.exists():
        msg = f"Input file not found: {input_path}"
        logger.error(msg)
        raise SystemExit(msg)

    logger.info(f"Translating {input_path.name} → {input_path.stem}_{lang}.pdf (lang={lang})")

    if chunk_size is None:
        return _translate_full(input_path, lang)
    else:
        return _translate_chunked(input_path, lang, chunk_size)


def _translate_full(input_path: Path, lang: str) -> Path:
    """Translate full PDF (original behavior)."""
    logger.info(f"Using Google Translate service. Large PDFs may take 5-20 min.")

    output_dir = input_path.parent / f"{input_path.stem}_{lang}_output"
    output_dir.mkdir(exist_ok=True)

    cmd = [
        "pdf2zh",
        str(input_path),
        "--service", "google",
        "-lo", lang,
        "--output", str(output_dir),
    ]

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    if log_level.startswith("DEBUG"):
        cmd.insert(1, "--debug")

    try:
        subprocess.run(cmd, check=True, timeout=1800)

        output_files = list(output_dir.glob("*-mono.pdf"))
        if not output_files:
            output_files = list(output_dir.glob("*.pdf"))
        if not output_files:
            msg = f"pdf2zh produced no output in {output_dir}"
            logger.error(msg)
            raise SystemExit(msg)

        mono_file = output_files[0]
        output_path = input_path.parent / f"{input_path.stem}_{lang}{input_path.suffix}"
        shutil.move(str(mono_file), str(output_path))
        shutil.rmtree(output_dir, ignore_errors=True)

        logger.info(f"Translation complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        msg = f"pdf2zh failed with exit code {e.returncode}. Check internet connection."
        logger.error(msg)
        raise SystemExit(msg)
    except subprocess.TimeoutExpired:
        msg = f"pdf2zh timeout (30 min). Large PDFs or slow network. Try --chunk-size N flag for batches."
        logger.error(msg)
        raise SystemExit(msg)


def _translate_chunked(input_path: Path, lang: str, chunk_size: int) -> Path:
    """Translate PDF in chunks and merge results."""
    total_pages = _get_page_count(input_path)
    logger.info(f"Using chunked translation: {total_pages} pages in batches of {chunk_size}")

    chunks_dir = input_path.parent / f"{input_path.stem}_{lang}_chunks"
    chunks_dir.mkdir(exist_ok=True)

    chunk_files = []
    log_level = os.environ.get("LOG_LEVEL", "INFO")

    try:
        for start in range(1, total_pages + 1, chunk_size):
            end = min(start + chunk_size - 1, total_pages)
            chunk_num = (start - 1) // chunk_size + 1
            total_chunks = (total_pages - 1) // chunk_size + 1

            chunk_out = chunks_dir / f"chunk_{start:04d}_{end:04d}-mono.pdf"

            if chunk_out.exists():
                logger.info(f"Chunk {chunk_num}/{total_chunks} ({start}-{end}) already translated, skipping")
                chunk_files.append(chunk_out)
                continue

            chunk_tmp_dir = chunks_dir / f"tmp_{start}_{end}"
            chunk_tmp_dir.mkdir(exist_ok=True)

            cmd = [
                "pdf2zh",
                str(input_path),
                "--service", "google",
                "-lo", lang,
                "--pages", f"{start}-{end}",
                "--output", str(chunk_tmp_dir),
            ]

            if log_level.startswith("DEBUG"):
                cmd.insert(1, "--debug")

            logger.info(f"Translating chunk {chunk_num}/{total_chunks} (pages {start}-{end} of {total_pages})")
            subprocess.run(cmd, check=True, timeout=1800)

            mono_files = list(chunk_tmp_dir.glob("*-mono.pdf"))
            if not mono_files:
                raise SystemExit(f"No output for chunk {start}-{end}")

            shutil.move(str(mono_files[0]), str(chunk_out))
            shutil.rmtree(chunk_tmp_dir, ignore_errors=True)
            chunk_files.append(chunk_out)
            logger.info(f"Chunk {chunk_num}/{total_chunks} complete")

        output_path = input_path.parent / f"{input_path.stem}_{lang}{input_path.suffix}"
        logger.info(f"Processing {len(chunk_files)} chunks for merge")

        trimmed_files = []
        for i, chunk_file in enumerate(chunk_files):
            chunk_num = i + 1
            start = (i * chunk_size) + 1
            end = min((i + 1) * chunk_size, total_pages)
            expected_pages = end - start + 1

            reader = PdfReader(str(chunk_file))
            chunk_pages = len(reader.pages)

            if chunk_pages == expected_pages:
                # pdf2zh --pages already produced correct page count, use directly
                logger.info(f"Chunk {chunk_num}: {chunk_pages} pages (correct), using directly")
                trimmed_files.append(chunk_file)
            elif chunk_pages == total_pages:
                # Full PDF, extract pages start-1 to end-1
                trimmed_file = chunks_dir / f"chunk_{start:04d}_{end:04d}_trimmed.pdf"
                writer = PdfWriter()
                for page_idx in range(start - 1, min(end, chunk_pages)):
                    writer.add_page(reader.pages[page_idx])
                with open(trimmed_file, "wb") as f:
                    writer.write(f)
                logger.info(f"Chunk {chunk_num}: {chunk_pages} pages (full PDF), extracted {expected_pages}")
                trimmed_files.append(trimmed_file)
            else:
                logger.warning(f"Chunk {chunk_num}: {chunk_pages} pages, expected {expected_pages} or {total_pages}")
                trimmed_files.append(chunk_file)

        logger.info(f"Merging {len(trimmed_files)} chunks → {output_path.name}")
        _merge_pdfs(trimmed_files, output_path)

        logger.info(f"Translation complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        msg = f"pdf2zh chunk failed with exit code {e.returncode}. Check internet connection."
        logger.error(msg)
        raise SystemExit(msg)
    except subprocess.TimeoutExpired:
        msg = f"Chunk timeout (30 min). Try smaller --chunk-size."
        logger.error(msg)
        raise SystemExit(msg)


def convert_pdf_to_markdown(pdf_path: Path, page_range: tuple[int, int] | None = None) -> Path:
    """Convert PDF to Markdown using Docling.

    Args:
        pdf_path: Path to PDF file
        page_range: Optional (start, end) tuple for page range (1-based, inclusive)

    Returns:
        Path to output Markdown file (same name, .md extension, or _pN_M.md if page range)

    Raises:
        SystemExit: If docling not installed or conversion fails
    """
    _check_deps(need_docling=True)

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        msg = f"Input PDF not found: {pdf_path}"
        logger.error(msg)
        raise SystemExit(msg)

    if page_range:
        start, end = page_range
        output_path = pdf_path.with_name(f"{pdf_path.stem}_p{start}_{end}.md")
    else:
        output_path = pdf_path.with_suffix(".md")

    range_str = f"pages {page_range[0]}-{page_range[1]}" if page_range else "full document"
    logger.info(f"Converting {pdf_path.name} ({range_str}) → {output_path.name}")

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        if page_range:
            result = converter.convert(str(pdf_path), page_range=page_range)
        else:
            result = converter.convert(str(pdf_path))
        md_content = result.document.export_to_markdown()

        output_path.write_text(md_content, encoding="utf-8")
        logger.info(f"Conversion complete: {output_path}")
        return output_path

    except ImportError as e:
        msg = f"Docling import failed: {e}"
        logger.error(msg)
        raise SystemExit(msg)
    except Exception as e:
        msg = f"Docling conversion failed: {e}"
        logger.error(msg)
        raise SystemExit(msg)


@click.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to input PDF file",
)
@click.option(
    "--translate",
    is_flag=True,
    default=False,
    help="Translate PDF to target language",
)
@click.option(
    "--lang",
    default="ru",
    show_default=True,
    help="Target language code for translation",
)
@click.option(
    "--markdown",
    "to_markdown",
    is_flag=True,
    default=False,
    help="Convert PDF(s) to Markdown",
)
@click.option(
    "--chunk-size",
    "chunk_size",
    default=None,
    type=int,
    help="Pages per translation batch for large PDFs (None = full file)",
)
@click.option(
    "--pages",
    "pages_str",
    default=None,
    help="Page range for markdown conversion (e.g. 1-20)",
)
def main(input_path: str, translate: bool, lang: str, to_markdown: bool, chunk_size: int | None, pages_str: str | None) -> None:
    """Translate PDF and/or convert to Markdown.

    Examples:
        # Translate only
        python tools/document_converter.py --input input.pdf --translate --lang ru

        # Convert to Markdown only
        python tools/document_converter.py --input input.pdf --markdown

        # Both operations
        python tools/document_converter.py --input input.pdf --translate --lang ru --markdown
    """
    if not translate and not to_markdown:
        click.echo("Error: specify at least --translate or --markdown", err=True)
        raise SystemExit(1)

    input_path = Path(input_path)
    results = []

    # Parse page range if provided
    page_range = None
    if pages_str:
        try:
            parts = pages_str.split("-")
            if len(parts) != 2:
                raise ValueError("Invalid format, use: 1-20")
            start, end = int(parts[0]), int(parts[1])
            if start < 1 or end < start:
                raise ValueError("Start must be >= 1 and <= end")
            page_range = (start, end)
        except ValueError as e:
            click.echo(f"Error: invalid --pages format: {e}", err=True)
            raise SystemExit(1)

    # Step 1: Translate if requested
    translated_path = None
    if translate:
        translated_path = translate_pdf(input_path, lang=lang, chunk_size=chunk_size)
        results.append(f"[+] Translated: {translated_path}")

    # Step 2: Convert original to Markdown if requested
    if to_markdown:
        md_path = convert_pdf_to_markdown(input_path, page_range=page_range)
        results.append(f"[+] Markdown: {md_path}")

        # Step 3: Convert translated to Markdown if translation exists
        if translated_path:
            md_translated = convert_pdf_to_markdown(translated_path, page_range=page_range)
            results.append(f"[+] Markdown (translated): {md_translated}")

    # Output summary
    for result in results:
        click.echo(result)


if __name__ == "__main__":
    main()
