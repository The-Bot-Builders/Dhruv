from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import hashlib

from langchain.utilities import ApifyWrapper
from langchain.document_loaders.base import Document

from processors.db import CONNECTION_STRING
from langchain.vectorstores.pgvector import PGVector

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

class URLProcessor:

    @staticmethod
    def process(url, index):
        index_md5 = hashlib.md5(index.encode()).hexdigest()

        apify = ApifyWrapper()

        loader = apify.call_actor(
            actor_id="apify/website-content-crawler",
            run_input={"startUrls": [{"url": url}], "maxRequestsPerCrawl": 1},
            dataset_mapping_function=lambda item: Document(
                page_content=item["text"] or "",
                metadata={"source": item["url"]}
            ),
            memory_mbytes=1024,
            timeout_secs=120
        )
        pages = loader.load_and_split()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = splitter.split_documents(pages)

        PGVector.from_documents(
            embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),
            documents=texts,
            collection_name=index_md5,
            pre_delete_collection=False,
            connection_string=CONNECTION_STRING
        )

# Used to testing
# if __name__ == "__main__":
#     URLProcessor.process("https://docs.apify.com/platform/integrations/langchain", "abc")