import os

from langchain.text_splitter import RecursiveCharacterTextSplitter

from processors.db import engine, text

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

import logging
logging.basicConfig(level=logging.INFO)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
            table_name = f"{client_id}"

            statement = f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    id BIGSERIAL PRIMARY KEY,
                    thread_id VARCHAR(1024),
                    content TEXT,
                    embeddings vector(384)
                )
            """
            conn.execute(text(statement))
            for txt in texts:
                statement = f"""
                    INSERT INTO {table_name} (
                        thread_id,
                        content,
                        embeddings
                    ) VALUES (
                        :thread_id,
                        :content,
                        :embeddings
                    )
                """
                conn.execute(
                    text(statement),
                    parameters={
                        'thread_id': thread_id,
                        'content': txt.page_content,
                        'embeddings': f"{embedding.embed_query(txt.page_content)}"
                    }
                )
            

    @staticmethod
    def get_from_index(client_id, thread_id, query):
        table_name = f"{client_id}"
        with engine.connect() as conn:
            statement = f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    id BIGSERIAL PRIMARY KEY,
                    thread_id VARCHAR(1024),
                    content TEXT,
                    embeddings vector(384)
                )
            """
            conn.execute(text(statement))
            
            embed_query = embedding.embed_query(query)
            statement = f"""
                SELECT content, 1 - (embeddings <=> :embeddings) AS similarity
                FROM {table_name}
                WHERE 1 - (embeddings <=> :embeddings) > 0.1 AND thread_id = :thread_id
                ORDER BY similarity DESC
                LIMIT 4
            """
            results = conn.execute(
                text(statement),
                parameters={
                    'embeddings': f"{embedding.embed_query(query)}",
                    'thread_id': thread_id
                }
            )

            documents = []
            for row in results.fetchall():
                documents.append(Document(page_content=row[0]))
            
            return documents
