from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import EMBEDDING_MODEL, CHROMA_DB_PATH
from core.logger import setup_logger

class VectorIndexer:
    def __init__(self):
        self.logger = setup_logger("indexer")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def index_file(self, file_path: Path) -> int:
        self.logger.info(f"Indexing: {file_path}")
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path), encoding='utf-8')
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_DB_PATH)
        )
        return len(chunks)
