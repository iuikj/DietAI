import os
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from shared.config.settings import settings
# from langchain_community.embeddings import OpenAIEmbeddings


@lru_cache(maxsize=1)
def rag_loader():
    persist_directory = settings.VECTOR_STORE_PATH
    embeddings = OpenAIEmbeddings()  # 这里后期可以根据 settings.EMBEDDINGS_MODEL 切换
    vector_store = Chroma(
        collection_name=settings.VECTOR_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    return vector_store
