from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import EMBEDDING_MODEL, CHROMA_DB_PATH
from core.logger import setup_logger

class Retriever:
    def __init__(self):
        self.logger = setup_logger("retriever")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=self.embeddings
        )
    
    def retrieve(self, query: str, k: int = 5) -> list:
        self.logger.info(f"Retrieving for: {query[:50]}...")
        docs = self.vector_store.similarity_search(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
