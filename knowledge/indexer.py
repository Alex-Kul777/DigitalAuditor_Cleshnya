from pathlib import Path
from typing import Optional
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
    
    def index_file(self, file_path: str | Path, doc_type: str = "evidence",
                   req_level: Optional[int] = None, task_name: Optional[str] = None,
                   authority: Optional[str] = None) -> int:
        file_path = Path(file_path)
        self.logger.info(f"Indexing: {file_path} (doc_type={doc_type}, req_level={req_level}, task_name={task_name})")

        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path), encoding='utf-8')

        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)

        # Add metadata to all chunks
        for chunk_idx, chunk in enumerate(chunks):
            if chunk.metadata is None:
                chunk.metadata = {}

            # Extract page number: real page from PDF, chunk index for TXT/MD
            page_number = chunk.metadata.get("page", chunk_idx)

            chunk.metadata.update({
                "doc_type": doc_type,
                "req_level": req_level,
                "source_filename": file_path.name,
                "page_number": page_number,
                "task_name": task_name,
                "authority": authority
            })

        vector_store = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=self.embeddings
        )
        vector_store.add_documents(chunks)

        self.logger.info(f"Indexed {len(chunks)} chunks with metadata")
        return len(chunks)

    def index_documents(self, documents: list, persona: Optional[str] = None,
                       doc_type: str = "evidence", req_level: Optional[int] = None,
                       task_name: Optional[str] = None, authority: Optional[str] = None) -> int:
        """Index a list of Document objects with metadata.

        Args:
            documents: List of LangChain Document objects to index
            persona: Optional persona identifier for metadata filtering (legacy)
            doc_type: Document type (evidence, regulatory, audit_standard, local_policy)
            req_level: Requirement level (1=regulatory, 2=audit_standard, 3=local_policy)
            task_name: Task identifier for evidence filtering
            authority: Authority/source (ISO, ISACA, FSTEC, Brink's, etc.)

        Returns:
            Number of chunks indexed
        """
        self.logger.info(f"Indexing {len(documents)} documents (doc_type={doc_type}, req_level={req_level}, task_name={task_name})")

        # Add metadata to all documents
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}

            # Legacy persona support
            if persona:
                doc.metadata["persona"] = persona

            # M_Evidence metadata schema
            doc.metadata.update({
                "doc_type": doc_type,
                "req_level": req_level,
                "task_name": task_name,
                "authority": authority
            })

        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        self.logger.debug(f"Split into {len(chunks)} chunks")

        # Preserve page_number: use existing or chunk index
        for chunk_idx, chunk in enumerate(chunks):
            if "page_number" not in chunk.metadata:
                chunk.metadata["page_number"] = chunk_idx

        # Get or create vector store and append documents
        vector_store = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=self.embeddings
        )
        vector_store.add_documents(chunks)

        self.logger.info(f"Indexed {len(chunks)} chunks")
        return len(chunks)
