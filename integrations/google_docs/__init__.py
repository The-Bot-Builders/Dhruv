"""
The GoogleDocsClient class is a subclass of OAuth2Client.
It handles authorization and token fetch for Confluence API.
"""
import os

from auth import OAuth2Client
# from requests_oauthlib import OAuth2Session
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleDocsClient(OAuth2Client):
    """GoogleDocsClient class to handle authorization and token fetch."""

    def __init__(self, state):
        self.state = state
        self.scopes = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly"
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
