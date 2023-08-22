"""
The ConfluenceClient class is a subclass of OAuth2Client.
It handles authorization and token fetch for Confluence API.
"""
import os
import re
import urllib.parse as urlparse

from bs4 import BeautifulSoup
from auth import OAuth2Client


# The ConfluenceClient class is a subclass of OAuth2Client.
class ConfluenceClient(OAuth2Client):
    """ConfluenceClient class to handle authorization and token fetch."""

    def __init__(self, state):
        self.state = state
        self.scopes = [
            'offline_access',
            'write:confluence-content',
            'read:confluence-space.summary',
            'write:confluence-file',
            'read:confluence-props',
            'write:confluence-props',
            'read:confluence-content.all',
            'read:confluence-content.summary',
            'search:confluence',
            'read:confluence-content.permission',
            'read:confluence-user',
            'read:confluence-groups',
            'readonly:content.attachment:confluence',
        ],
        self.base_api_url = None
        self.integration = 'confluence'
        super().__init__(
            client_id=os.getenv('CONFLUENCE_CLIENT_ID'),
            client_secret=os.getenv('CONFLUENCE_CLIENT_SECRET'),
            authorization_base_url=os.getenv('CONFLUENCE_BASE_URL'),
            token_url=os.getenv('CONFLUENCE_TOKEN_URL'),
            redirect_uri=os.getenv('CONFLUENCE_REDIRECT_URI'),
            scopes=self.scopes,
            state=self.state,
            integration=self.integration
        )

    def get_authorization_url(self) -> str:
        """Get the authorization URL to redirect the user."""
        authorization_url = self._get_authorization_url(access_type="offline", prompt="consent")
        return authorization_url

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

    def _set_base_api_url(self, page_url):
        parsed_url = urlparse.urlparse(page_url)
        self.base_api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wiki"

    def get_page_content(self, page_id):
        url = f'{self.base_api_url}/rest/api/content/{page_id}?expand=body.storage'
        response = self.request('GET', url)
        print(response.content)
        response_data = response.json()

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response_data.get('message')}")
            return None

        html_content = response_data['body']['storage']['value']
        return self.html_to_text(html_content)

    def fetch_content_from_url(self, url):
        self._set_base_api_url(url)
        page_id = re.search(r'/pages/([0-9]+)/', url).group(1)

        return self.get_page_content(page_id)
