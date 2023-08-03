import re
import requests
from bs4 import BeautifulSoup
import base64


class ConfluenceClient:
    def __init__(self, domain, username, api_token):
        self.base_url = f'https://{domain}.atlassian.net/wiki/rest/api'
        credentials = f"{username}:{api_token}".encode('utf-8')
        encoded_credentials = base64.b64encode(credentials).decode('utf-8')

        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Accept': 'application/json'
        }


    @staticmethod
    def is_confluence_page_url(url):
        pattern = re.compile(r'https://[a-zA-Z0-9-]+\.atlassian\.net/wiki/spaces/.+/pages/[0-9]+/.+')
        return bool(pattern.match(url))

    def html_to_text(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
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
        return text

    def get_page_content(self, page_id):
        endpoint = f'{self.base_url}/content/{page_id}?expand=body.storage'
        response = requests.get(endpoint, headers=self.headers)
        response_data = response.json()

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response_data.get('message')}")
            return None

        html_content = response_data['body']['storage']['value']
        return self.html_to_text(html_content)

    def fetch_content_from_url(self, url):
        if not self.is_confluence_url(url):
            print("This is not a Confluence URL.")
            return None
        elif not self.is_confluence_page_url(url):
            print("This URL is not a Confluence page.")
            return None
        else:
            page_id = re.search(r'/pages/([0-9]+)/', url).group(1)
            return self.get_page_content(page_id)


# Usage:

# client = ConfluenceClient(domain=os.getenv('CONFLUENCE_DOMAIN'), username=os.getenv('CONFLUENCE_USERNAME'),
#                           api_token=os.getenv('CONFLUENCE_API_TOKEN'))
# url = input("Enter the Confluence URL: ")
# content = client.fetch_content_from_url(url)
# if content:
#     print("Page Content:", content)
