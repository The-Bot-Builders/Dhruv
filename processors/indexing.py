from langchain.text_splitter import RecursiveCharacterTextSplitter

from processors.db import DB
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

import logging
logging.basicConfig(level=logging.INFO)

class Indexing:

    @staticmethod
    def save_in_index(client_id, thread_id, pages):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = splitter.split_documents(pages)

        PGVector.from_documents(
            embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),
            documents=texts,
            collection_name=thread_id,
            pre_delete_collection=False,
            connection_string=DB.get_connection_string(client_id)
        )

    @staticmethod
    def get_from_index(client_id, thread_id, text):
        retriever = PGVector.from_existing_index(
            embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),
            collection_name=thread_id,
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection = False,
            connection_string=DB.get_connection_string(client_id),
        )

        return retriever.similarity_search(text, k=20)
    
    @staticmethod
    def get_retriever(client_id, thread_id):
        retriever = PGVector.from_existing_index(
            embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),
            collection_name=thread_id,
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection = False,
            connection_string=DB.get_connection_string(client_id),
        )
        
        return retriever.as_retriever()