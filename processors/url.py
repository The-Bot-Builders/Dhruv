import os
import hashlib
from urllib.parse import urlparse
import requests
import time

import logging
logging.basicConfig(level=logging.INFO)

from langchain.utilities import ApifyWrapper
from langchain.document_loaders.base import Document

from processors.db import CONNECTION_STRING
from langchain.vectorstores.pgvector import PGVector

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

from langchain.document_loaders import TextLoader
from .file import TempFileManager

class URLProcessor:

    @staticmethod
    def process(url, index):
        index_md5 = hashlib.md5(index.encode()).hexdigest()

        (url_type, parsed_url) = determine_url_type(url)
        
        pages = []
        if url_type == "notion":
            pages = get_pages_from_notion(url, parsed_url)
        elif url_type == "apify":
            pages = get_pages_from_apify(url, parsed_url)
        elif url_type == "soup":
            pages = get_pages_from_soup(url, parsed_url)

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

def determine_url_type(url):
    parsed_url = urlparse(url)

    if parsed_url.netloc == "www.notion.so":
        return ("notion", parsed_url)
    else:
        return ("apify", parsed_url)

def get_pages_from_apify(url, parsed_url):
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
    return pages

def get_pages_from_notion(url, parsed_url):
    page_id = parsed_url.path.split("/")[-1].split("-")[-1]

    if os.environ.get("STAGE", "local") != "local":
       return []

    with TempFileManager(page_id) as (temp_file_path, temp_file):
        headers = {
            'Authorization': f"Bearer {os.environ.get('NOTION_API_KEY')}", 
            'Notion-Version': '2022-02-22'
        }
        start_cursor = None
        while True:
            notion_url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            notion_url = notion_url + f"&start_cursor={start_cursor}" if start_cursor else notion_url
            response = requests.get(
                    notion_url,
                    headers=headers
                )
            response_as_json = response.json()
            for page in response_as_json["results"]:
                page_type = page["type"]
                if "rich_text" in page[page_type] and page[page_type]["rich_text"]:
                    for text in page[page_type]["rich_text"]:
                        temp_file.write(bytes(text["plain_text"] + " ", 'utf-8'))
            
            if response_as_json["has_more"]:
                start_cursor = response_as_json["next_cursor"]
            else:
                break
        
        temp_file.flush()
        
        loader = TextLoader(temp_file_path)
        pages = loader.load()
        
        return pages
        
def get_pages_from_soup(url):
    pass

# Used to testing
# if __name__ == "__main__":
#     URLProcessor.process("https://docs.apify.com/platform/integrations/langchain", "abc")