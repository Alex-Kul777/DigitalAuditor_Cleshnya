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
    
    def retrieve(self, query: str, k: int = 5, filter=None, exclude_personas=None) -> list:
        self.logger.info(f"Retrieving for: {query[:50]}...")

        # Determine how many results to fetch
        fetch_k = k * 3 if exclude_personas else k

        # Call similarity_search with filter if provided
        try:
            docs = self.vector_store.similarity_search(query, k=fetch_k, filter=filter)
        except TypeError:
            # Fallback for older Chroma versions that use 'where' instead of 'filter'
            docs = self.vector_store.similarity_search(query, k=fetch_k)

        # Post-filter to exclude personas (if specified)
        if exclude_personas:
            docs = [doc for doc in docs if doc.metadata.get('persona') not in exclude_personas]
            docs = docs[:k]  # Take only k results
            self.logger.info(f"Filtered {len(docs)} results (excluded {len(exclude_personas)} personas)")

        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
