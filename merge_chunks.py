#!/usr/bin/env python3
from pathlib import Path
from pypdf import PdfReader, PdfWriter

chunks_dir = Path("/home/kap/projects/DigitalAuditor_Cleshnya/personas/CISA/raw/CISA Review Manual_ru_chunks")
output_path = Path("/home/kap/projects/DigitalAuditor_Cleshnya/personas/CISA/raw/CISA Review Manual_ru.pdf")

# Find all chunk files
chunk_files = sorted(chunks_dir.glob("chunk_*-mono.pdf"))
print(f"Found {len(chunk_files)} chunks")

trimmed_files = []
chunk_size = 50

for i, chunk_file in enumerate(chunk_files):
    chunk_num = i + 1
    start = (i * chunk_size) + 1
    end = (i + 1) * chunk_size

    # Parse actual range from filename
    filename = chunk_file.name
    parts = filename.split('_')
    start = int(parts[1])
    end = int(parts[2].split('-')[0])

    trimmed_file = chunks_dir / f"chunk_{start:04d}_{end:04d}_trimmed.pdf"

    print(f"Extracting chunk {chunk_num}: pages {start}-{end} from {filename}")

    reader = PdfReader(str(chunk_file))
    writer = PdfWriter()

    # Extract only pages in range (convert 1-indexed to 0-indexed)
    for page_idx in range(start - 1, min(end, len(reader.pages))):
        writer.add_page(reader.pages[page_idx])

    with open(trimmed_file, "wb") as f:
        writer.write(f)

    pages_extracted = min(end, len(reader.pages)) - (start - 1)
    print(f"  → Extracted {pages_extracted} pages to {trimmed_file.name}")
    trimmed_files.append(trimmed_file)

print(f"\nMerging {len(trimmed_files)} trimmed chunks...")
writer = PdfWriter()
for trimmed_file in trimmed_files:
    writer.append(str(trimmed_file))

with open(output_path, "wb") as f:
    writer.write(f)

# Count final pages
final_reader = PdfReader(str(output_path))
final_pages = len(final_reader.pages)

print(f"✅ Merged PDF: {output_path}")
print(f"   Total pages: {final_pages}")
print(f"   File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
