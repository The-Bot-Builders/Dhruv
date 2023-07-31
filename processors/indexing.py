import os

from langchain.text_splitter import RecursiveCharacterTextSplitter

from processors.db import DB
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy

from langchain.vectorstores import Qdrant
from qdrant_client.models import Distance, VectorParams

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

import logging
logging.basicConfig(level=logging.INFO)

RETRIEVER_DATABASE = os.environ.get('RETRIEVER_DATABASE', 'pg')

embedding = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

class Indexing:

    @staticmethod
    def save_in_index(client_id, thread_id, pages):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = splitter.split_documents(pages)

        if RETRIEVER_DATABASE == 'qdrant':
            from .qdrant import client

            try: 
                client.get_collection(f"{client_id}_{thread_id}")
            except Exception as e:
                client.recreate_collection(
                    f"{client_id}_{thread_id}",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )

            doc_store = Qdrant(
                client=client, 
                collection_name=f"{client_id}_{thread_id}", 
                embeddings=embedding,
            )
            doc_store.add_documents(texts)
        else:
            PGVector.from_documents(
                embedding=embedding,
                documents=texts,
                collection_name=thread_id,
                pre_delete_collection=False,
                connection_string=DB.get_connection_string(client_id)
            )

    @staticmethod
    def get_from_index(client_id, thread_id, text):
        vector_store = Indexing.vector_store(client_id, thread_id)
        
        return vector_store.similarity_search(text, k=1)
    
    @staticmethod
    def get_retriever(client_id, thread_id):
        vector_store = Indexing.vector_store(client_id, thread_id)
        
        return vector_store.as_retriever()

    @staticmethod
    def vector_store(client_id, thread_id):
        retriever = None

        if RETRIEVER_DATABASE == 'qdrant':
            from .qdrant import client

            retriever = Qdrant(
                client=client, 
                collection_name=f"{client_id}_{thread_id}", 
                embeddings=embedding,
            )
        else:
            retriever = PGVector.from_existing_index(
                embedding=embedding,
                collection_name=thread_id,
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection = False,
                connection_string=DB.get_connection_string(client_id),
            )
        
        return retriever