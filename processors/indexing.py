import os

from langchain.text_splitter import RecursiveCharacterTextSplitter

from processors.db import engine, text

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

import logging
logging.basicConfig(level=logging.INFO)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

TABLE_NAME = "embeddings"

embedding = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

class Indexing:

    @staticmethod
    def save_in_index(client_id, thread_id, pages):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = splitter.split_documents(pages)

        with engine.connect() as conn:
            for txt in texts:
                statement = f"""
                    INSERT INTO {TABLE_NAME} (
                        client_id,
                        thread_id,
                        content,
                        embeddings
                    ) VALUES (
                        :client_id,
                        :thread_id,
                        :content,
                        :embeddings
                    )
                """
                conn.execute(
                    text(statement),
                    parameters={
                        'client_id': client_id,
                        'thread_id': thread_id,
                        'content': txt.page_content,
                        'embeddings': f"{embedding.embed_query(txt.page_content)}"
                    }
                )
            

    @staticmethod
    def get_from_index(client_id, thread_id, query):
        with engine.connect() as conn:
            embed_query = embedding.embed_query(query)
            statement = f"""
                SELECT content, 1 - (embeddings <=> :embeddings) AS similarity
                FROM {TABLE_NAME}
                WHERE 1 - (embeddings <=> :embeddings) > 0.2 AND thread_id = :thread_id AND client_id = :client_id
                ORDER BY similarity DESC
                LIMIT 10
            """
            results = conn.execute(
                text(statement),
                parameters={
                    'embeddings': f"{embedding.embed_query(query)}",
                    'client_id': client_id,
                    'thread_id': thread_id
                }
            )

            documents = []
            for row in results.fetchall():
                documents.append(Document(page_content=row[0]))
            
            return documents
