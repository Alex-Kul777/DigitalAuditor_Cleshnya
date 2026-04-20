import pytest
from knowledge.retriever import Retriever

def test_retriever_init():
    retriever = Retriever()
    assert retriever is not None
