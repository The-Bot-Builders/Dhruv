"""
The GoogleDocsClient class is a subclass of OAuth2Client.
It handles authorization and token fetch for Confluence API.
"""
import os
import re

import requests

from auth import OAuth2Client
# from requests_oauthlib import OAuth2Session
from google_auth_oauthlib.flow import InstalledAppFlow
from urllib.parse import urlparse


def parse_paragraph(element):
    # Parse a paragraph element
    text = ""
    for content in element['paragraph']['elements']:
        if 'textRun' in content:
            text += content['textRun']['content']
    return text

def parse_heading(element):
    # Parse a heading element
    level = element['paragraph']['paragraphStyle']['headingLevel']
    text = parse_paragraph(element)
    return f"<h{level}>{text}</h{level}>"

def parse_elements(elements):
    # Parse a list of elements
    parsed_content = ""
    for element in elements:
        if 'paragraph' in element:
            parsed_content += parse_paragraph(element)
        # elif 'paragraphStyle' in element['tableOfContents']:
        #     parsed_content += parse_heading(element)
    return parsed_content


class GoogleDocsClient(OAuth2Client):
    """GoogleDocsClient class to handle authorization and token fetch."""

    def __init__(self, state):
        self.state = state
        self.scopes = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/documents.readonly",
            # "https://www.googleapis.com/auth/drive",
            # "https://www.googleapis.com/auth/drive.file",
            # "https://www.googleapis.com/auth/drive.readonly"
        ]
        self.base_api_url = 'https://docs.googleapis.com/v1/documents/'
        self.integration = 'google_docs'
        super().__init__(
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            authorization_base_url=os.getenv('GOOGLE_BASE_URL'),
            token_url=os.getenv('GOOGLE_TOKEN_URL'),
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            scopes=self.scopes,
            state=self.state,
            integration=self.integration
        )

    def get_authorization_url(self) -> str:
        """Get the authorization URL to redirect the user."""
        flow = InstalledAppFlow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "auth_uri": self.authorization_base_url,
                    "token_uri": self.token_url,
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        print(self.redirect_uri)
        # Generate the authorization URL
        authorization_url, _ = flow.authorization_url(

            state=self.state,
            # You can customize additional parameters here if needed
            access_type='offline', prompt='consent'
        )
        return authorization_url

    def _get_document_id(self, docs_url):
        # Define a regular expression pattern to match the document ID
        pattern = r"document/d/([a-zA-Z0-9-_]+)"

        # Find the document ID using the regular expression
        match = re.search(pattern, docs_url)

        if match:
            document_id = match.group(1)
            print("Document ID:", document_id)
            return document_id
        else:
            print("Document ID not found.")
            return None

    def get_document_content(self, docs_url):

        # Parse the URL
        document_id = self._get_document_id(docs_url)


        print("Document ID:", document_id)
        url = f"{self.base_api_url}{document_id}"

        token = self.get_token()

        # Set the Authorization header with the access token
        headers = {
            "Authorization": f"Bearer {token['access_token']}"
        }

        # Make the API request
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            document_data = response.json()
            parsed_content = parse_elements(document_data['body']['content'])

            print("Document Data:", parsed_content)
            return parsed_content
        else:
            print("Error:", response.status_code, response.text)
            return None
