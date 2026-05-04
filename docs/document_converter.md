# Document Converter — PDF Translation & Markdown Conversion

## Overview

**Purpose:** Automate PDF translation and Markdown conversion for audit document processing.

**When to use:**
- Translate English-language standards (CISA, IIA, ISO) to Russian
- Convert PDFs to Markdown for ChromaDB indexing
- Combine both operations in a single workflow

**Features:**
- Translate PDFs via `pdf2zh` (powered by GigaChat)
- Convert PDFs to Markdown via Docling (IBM)
- Independent, composable operations (translate only, convert only, or both)
- Output files saved in same directory as input PDF

---

## Installation

Install required dependencies:

```bash
pip install pdf2zh docling
```

Both packages are included in `requirements.txt`. After adding them, run:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# GigaChat API credentials (required for translation)
GIGACHAT_API_KEY=your_api_key_here
GIGACHAT_BASE_URL=https://api.gigachat.ru/api/v1
GIGACHAT_MODEL=GigaChat-2-Max
```

**For translate operations:**
- `GIGACHAT_API_KEY` — Required. GigaChat API key.
- `GIGACHAT_BASE_URL` — Optional. Defaults to `https://api.gigachat.ru/api/v1`.
- `GIGACHAT_MODEL` — Optional. Defaults to `GigaChat-2-Max`. Alternatives: `GigaChat-2-Lite`.

**For Markdown conversion:**
- No additional configuration needed. Docling works offline.

---

## Usage

### Via `main.py` (Recommended)

#### Example 1: Translate Only

Translate English PDF to Russian:

```bash
python main.py convert \
  --input "personas/CISA/raw/CISA Review Manual.pdf" \
  --translate --lang ru
```

**Output:**
- `personas/CISA/raw/CISA Review Manual_ru.pdf`

#### Example 2: Convert to Markdown Only

Convert PDF to Markdown (English):

```bash
python main.py convert \
  --input "personas/CISA/raw/CISA Review Manual.pdf" \
  --markdown
```

**Output:**
- `personas/CISA/raw/CISA Review Manual.md`

#### Example 3: Both Operations

Translate to Russian AND convert both PDFs to Markdown:

```bash
python main.py convert \
  --input "personas/CISA/raw/CISA Review Manual.pdf" \
  --translate --lang ru \
  --markdown
```

**Output:**
- `personas/CISA/raw/CISA Review Manual_ru.pdf` (translated)
- `personas/CISA/raw/CISA Review Manual.md` (original as MD)
- `personas/CISA/raw/CISA Review Manual_ru.md` (translated as MD)

---

### Via Standalone CLI

Run directly without `main.py`:

```bash
python tools/document_converter.py \
  --input "personas/CISA/raw/CISA Review Manual.pdf" \
  --translate --lang ru --markdown
```

Same options and behavior as `main.py convert`.

---

## Output File Naming

| Operation | Input | Output |
|-----------|-------|--------|
| Translate | `document.pdf` | `document_<lang>.pdf` (e.g., `document_ru.pdf`) |
| Markdown (original) | `document.pdf` | `document.md` |
| Markdown (translated) | `document_ru.pdf` | `document_ru.md` |

All output files are saved in the **same directory** as the input PDF.

---

## Supported Languages

`pdf2zh` supports any language code. Common ones:

| Language | Code |
|----------|------|
| Russian | `ru` |
| English | `en` |
| Chinese (Simplified) | `zh` |
| Spanish | `es` |
| French | `fr` |
| German | `de` |

Use `--lang <code>` to specify. Default is `ru` (Russian).

---

## Command-Line Options

### `python main.py convert`

```
--input TEXT         Path to input PDF file [required]
--translate          Translate PDF to target language [flag]
--lang TEXT          Target language code [default: ru]
--markdown           Convert PDF(s) to Markdown [flag]
--help               Show help message
```

### Minimal Usage

At least one of `--translate` or `--markdown` is required:

```bash
# Error: neither flag specified
python main.py convert --input file.pdf

# OK: translate only
python main.py convert --input file.pdf --translate

# OK: convert only
python main.py convert --input file.pdf --markdown

# OK: both
python main.py convert --input file.pdf --translate --markdown
```

---

## Troubleshooting

### Error: `Missing dependencies: pdf2zh`

**Cause:** `pdf2zh` not installed.

**Solution:**
```bash
pip install pdf2zh
```

### Error: `Missing dependencies: docling`

**Cause:** `docling` not installed.

**Solution:**
```bash
pip install docling
```

### Error: `GIGACHAT_API_KEY not set`

**Cause:** `.env` missing `GIGACHAT_API_KEY` or environment variable not loaded.

**Solution:**
1. Check `.env` file exists in project root
2. Set `GIGACHAT_API_KEY=<your_key>`
3. Reload environment:
   ```bash
   source .env  # On Linux/Mac
   # Or on Windows: set $(cat .env | grep GIGACHAT_API_KEY)
   ```

### Error: `pdf2zh failed: ...`

**Cause:** GigaChat API error (invalid key, rate limit, network issue).

**Solution:**
1. Verify `GIGACHAT_API_KEY` is correct
2. Check GigaChat API status
3. Try again after a few seconds (rate limit)
4. Verify internet connection

### Error: `Input file not found`

**Cause:** PDF path doesn't exist.

**Solution:**
- Use absolute path: `/home/user/projects/file.pdf`
- Or relative from project root: `personas/CISA/raw/CISA Review Manual.pdf`
- Check path is correct: `ls <path>`

### Docling Conversion Slow

**Cause:** Docling processes PDFs locally (CPU-intensive).

**Workaround:** Patience. Large PDFs (100+ pages) take 1-2 minutes.

---

## Integration with Audit Workflow

### Step-by-Step Example

1. **Create audit task:**
   ```bash
   python main.py create --name cisa_audit --company "Test Corp"
   ```

2. **Download English PDF** to `personas/CISA/raw/CISA Review Manual.pdf`

3. **Translate and convert:**
   ```bash
   python main.py convert \
     --input "personas/CISA/raw/CISA Review Manual.pdf" \
     --translate --lang ru --markdown
   ```

4. **Index Markdown files** in ChromaDB:
   ```bash
   # Copy .md files to task evidence
   cp personas/CISA/raw/*.md tasks/instances/cisa_audit/evidence/
   
   # Run audit (will index all files in evidence/)
   python main.py run --task cisa_audit
   ```

---

## Limitations

- **PDF complexity:** Scanned PDFs or PDFs with complex layouts may not convert perfectly
- **Translation quality:** Depends on GigaChat model version (check `GIGACHAT_MODEL`)
- **File size:** Very large PDFs (500+ pages) may timeout or hit API limits
- **Language support:** Some languages may not translate well; test with small sections first

---

## Performance Notes

| Operation | Time | Notes |
|-----------|------|-------|
| Translate (100 pages) | 10-20 min | GigaChat API response time, 30 min timeout |
| Translate (full CISA manual, 1200+ pages) | 30+ min | May hit timeout; use `--pages N` for subsets |
| Convert to MD (100 pages) | 2-5 min | CPU-bound, runs locally |
| Both operations | 15-30 min | Sequential: translate + convert |

**GigaChat Integration:**
- Timeout: 30 minutes (increased from 5 min for large documents)
- Large PDFs (500+ pages) may timeout — consider translating in chunks with `--pages`
- Check `GIGACHAT_API_KEY` and API quota if translation fails
- Enable `--log-level DEBUG-1` or higher to see pdf2zh debug output

---

## See Also

- `CLAUDE.md` — Project setup and architecture
- `README.md` — Feature overview
- `ROADMAP.md` — M_Converter milestone
