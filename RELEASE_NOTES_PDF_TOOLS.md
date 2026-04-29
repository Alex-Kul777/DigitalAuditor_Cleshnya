# PDF Translation & Markdown Conversion Release

**Version**: 1.0.0  
**Date**: 2026-04-29  
**Commit**: 275c18a

## Features

### ✅ PDF Translation (`translate_pdf()`)
- **Framework**: PDFMathTranslate (pdf2zh) + Google Translate
- **Modes**: Full document or chunked (for large PDFs)
- **Resume**: Intermediate chunks cached, can resume on failure
- **Timeout**: 30 minutes per chunk, with fallback

**Usage**:
```bash
python main.py convert --input document.pdf --translate --lang ru
```

### ✅ PDF → Markdown Conversion (`convert_pdf_to_markdown()`)
- **Engine**: Docling (IBM) + RapidOCR
- **Architecture**: Subprocess isolation (guarantees memory reclaim + hard timeout)
- **Chunking**: 50-page chunks with per-page fallback on timeout
- **Resume**: Intermediate results cached in `chunks/` directory
- **Timeout**: 600s (10 min) per chunk, 120s per page

**Usage**:
```bash
python main.py convert --input document.pdf --markdown
```

### ✅ Combined Operation
```bash
python main.py convert --input document.pdf --translate --lang ru --markdown
```

Produces:
- `document_ru.pdf` (translated)
- `document.md` (original → Markdown)
- `document_ru.md` (translated → Markdown)

## Verified Files

| File | Type | Size | Pages | Status |
|------|------|------|-------|--------|
| CISA Review Manual.pdf | EN Original | 13 MB | 1232 | ✅ Converted |
| CISA Review Manual_ru.pdf | RU Translated | 19 MB | 1232 | ✅ Converted |
| CISA Review Manual.md | EN Markdown | 1.9 MB | 8673 lines | ✅ Indexed |
| CISA Review Manual_ru.md | RU Markdown | 3.2 MB | 16393 lines | ✅ Indexed |

## Configuration

### Dependencies
- `pdf2zh>=1.0.0` (PDFMathTranslate framework)
- `docling>=2.0.0` (IBM document converter)
- `pypdf>=4.0.0` (PDF manipulation)
- `click>=8.1.0` (CLI framework)

### .gitignore Rules
```
# Exclude PDFs (large, sensitive)
personas/*/raw/*.pdf

# But include Markdown versions
!personas/*/raw/*.md
```

## Testing

**Test Suite**: 8 tests for document converter module

```bash
python -m pytest tests/tools/test_document_converter.py -v
```

**Results**: ✅ 8/8 PASSED
- Dependency checking (docling, pdf2zh)
- Markdown conversion (page range, output validation)
- .gitignore rules verification
- CLI integration tests

## Known Limitations

1. **pdf2zh requires internet**: Uses Google Translate API (service: google)
   - Fallback needed for offline mode (Xinference/Ollama)
   - Timeout: 30 minutes per full document

2. **Large PDFs**: Memory intensive during processing
   - Solution: Use `--chunk-size N` flag to break into smaller batches
   - Recommended: 50-100 page chunks for 1000+ page documents

3. **RapidOCR language**: Currently set to Chinese models
   - Works for English/Russian via character recognition
   - Best quality for CJK text

## Future Improvements

- [ ] Add support for local translation (Xinference)
- [ ] Configurable chunk size in config.yaml
- [ ] Direct ChromaDB indexing (skip intermediate MD files)
- [ ] Progress bar for large conversions
- [ ] Parallel chunk processing (thread pool)

## Architecture Notes

### Subprocess Isolation
Used instead of threading to:
- Guarantee memory reclaim from native Docling C-extensions
- Enforce hard timeout via SIGKILL (not just thread join)
- Allow per-page fallback when chunks fail

**Worker**: `tools/docling_worker.py`
- Called once per chunk/page
- Subprocess exits → OS reclaims all memory
- JSON output via tempfile

### Resume Capability
Intermediate results saved per chunk:
```
personas/CISA/raw/chunks/CISA_Review_Manual_chunks/
├── chunk_001_p1_50.md
├── chunk_002_p51_100.md
├── page_0001.md  (fallback, if chunk timeout)
└── ...
```

On restart, existing chunks skipped automatically.

## Release Checklist

- [x] Code implemented & tested
- [x] CLI integrated into main.py
- [x] Dependencies added to requirements.txt
- [x] .gitignore rules configured
- [x] CISA PDFs converted & indexed
- [x] Test suite added (8 tests)
- [x] Documentation (this file)
- [x] Git commit created

## Support

Questions? Check:
- `tools/document_converter.py` — source code
- `tests/tools/test_document_converter.py` — test examples
- `CLAUDE.md` — project guidelines
