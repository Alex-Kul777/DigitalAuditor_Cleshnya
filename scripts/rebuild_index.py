#!/usr/bin/env python3
import sys
from pathlib import Path

# Добавить корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.indexer import VectorIndexer

def main():
    indexer = VectorIndexer()
    raw_docs = Path("knowledge/raw_docs")
    
    for file_path in raw_docs.glob("*"):
        if file_path.is_file() and file_path.name != ".gitkeep":
            print(f"Indexing: {file_path.name}")
            chunks = indexer.index_file(file_path)
            print(f"  -> {chunks} chunks indexed")

if __name__ == "__main__":
    main()
