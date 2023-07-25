import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from langchain.document_loaders import TextLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import PyPDFLoader

from processors.db import CONNECTION_STRING
from langchain.vectorstores.pgvector import PGVector

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

class TempFileManager:

    def __init__(self, filename):
        self.file_path = f'temporary/{filename}'

    def __enter__(self):
        self.file_obj  = open(self.file_path, 'wb+')
        return (self.file_path, self.file_obj)
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.file_obj:
            self.file_obj.close()
        os.remove(self.file_path)

class FileProcessor:

    @staticmethod
    def process(file_type, file_path, index):
        index_md5 = hashlib.md5(index.encode()).hexdigest()

        texts = None

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        if (file_type == 'pdf'):
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            texts = splitter.split_documents(pages)
        
        elif (file_type == "text"):
            loader = TextLoader(file_path)
            pages = loader.load()
            texts = splitter.split_documents(pages)

        else:
            return False

        if texts is None:
            return False

        PGVector.from_documents(
            embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),
            documents=texts,
            collection_name=index_md5,
            connection_string=CONNECTION_STRING,
        )
        return True

# Used for testing
# if __name__ == "__main__":
#     with TempFileManager('test.txt') as f:
#         f.write(b'Hello World')
#         f.seek(0)
#         print(f.read())
