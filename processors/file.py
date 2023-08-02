import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from langchain.document_loaders import TextLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import PyPDFLoader

from .indexing import Indexing

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
    def process(file_type, file_path, index, client_id):
        index_md5 = hashlib.md5(index.encode()).hexdigest()
        document_md5 = hashlib.md5(file_path.encode()).hexdigest()

        pages = None
        
        if (file_type == 'pdf'):
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
        
        elif (file_type == "text"):
            loader = TextLoader(file_path)
            pages = loader.load()
        else:
            return False

        if pages is None:
            return False

        Indexing.save_in_index(client_id, index_md5, pages)

        return True

# Used for testing
# if __name__ == "__main__":
#     with TempFileManager('test.txt') as f:
#         f.write(b'Hello World')
#         f.seek(0)
#         print(f.read())
