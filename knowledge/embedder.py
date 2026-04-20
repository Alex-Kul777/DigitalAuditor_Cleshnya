from langchain_community.embeddings import HuggingFaceEmbeddings
from core.config import EMBEDDING_MODEL

def get_embedder():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
