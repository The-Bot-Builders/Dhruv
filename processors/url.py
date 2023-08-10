import os
import hashlib
from urllib.parse import urlparse
import requests
import time

import logging
logging.basicConfig(level=logging.INFO)

from .indexing import Indexing
from .file import TempFileManager
from .integrations import NotionIntegration

from langchain.utilities import ApifyWrapper
from langchain.document_loaders.base import Document

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.document_loaders import TextLoader

from bs4 import BeautifulSoup

class URLProcessor:

    @staticmethod
    def process(url, index, client_id):
        index_md5 = hashlib.md5(index.encode()).hexdigest()
        document_md5 = hashlib.md5(url.encode()).hexdigest()

        (url_type, parsed_url) = URLProcessor.determine_url_type(url)
        
        pages = []
        if url_type == "notion":
            pages = URLProcessor.get_pages_from_notion(client_id, url, parsed_url)
        elif url_type == "web":
            pages = URLProcessor.get_pages_from_web(client_id, url, parsed_url)

        Indexing.save_in_index(client_id, index_md5, pages)

    @staticmethod       
    def determine_url_type(url):
        parsed_url = urlparse(url)

        if parsed_url.netloc == "www.notion.so":
            return ("notion", parsed_url)
        else:
            return ("web", parsed_url)

    @staticmethod
    def get_pages_from_web(client, url, parsed_url):
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        for undesired_div in ["sidebar", "header", "footer"]:
            [
                tag.extract()
                for tag in soup.find_all(
                    "div", class_=lambda x: x and undesired_div in x.split()
                )
            ]
        for undesired_tag in [
                "nav",
                "header",
                "footer",
                "meta",
                "script",
                "style",
            ]:
                [tag.extract() for tag in soup.find_all(undesired_tag)]

        text = soup.get_text("\n")
        return [Document(page_content=text, metadata={"source": url})]

        # apify = ApifyWrapper()

        # loader = apify.call_actor(
        #     actor_id="apify/website-content-crawler",
        #     run_input={"startUrls": [{"url": url}], "maxRequestsPerCrawl": 1},
        #     dataset_mapping_function=lambda item: Document(
        #         page_content=item["text"] or "",
        #         metadata={"source": item["url"]}
        #     ),
        #     memory_mbytes=1024,
        #     timeout_secs=120
        # )
        # pages = loader.load_and_split()
        # return pages

    @staticmethod
    def get_pages_from_notion(client_id, url, parsed_url):
        page_id = parsed_url.path.split("/")[-1].split("-")[-1]

        if os.environ.get("STAGE", "local") != "local":
            return []

        with TempFileManager(page_id) as (temp_file_path, temp_file):

            access_token = NotionIntegration.get_access_token(client_id)
            headers = {
                'Authorization': f"Bearer {access_token}", 
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

    @staticmethod        
    def get_pages_from_soup(url):
        pass

# Used to testing
# if __name__ == "__main__":
#     URLProcessor.process("https://docs.apify.com/platform/integrations/langchain", "abc")