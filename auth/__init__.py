"""
Auth class to handle authorization and token fetch.
"""
import os
from datetime import datetime
import warnings


from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session


from dotenv import load_dotenv, find_dotenv

ENV_FILE = '.prod.env' if os.environ.get('STAGE', 'local') == 'prod' else '.local.env'
load_dotenv(find_dotenv(filename=ENV_FILE))

from .token_management import store_encrypted_token, retrieve_decrypted_token




class OAuth2Client:
    def __init__(self, client_id, client_secret, authorization_base_url, token_url, redirect_uri, scopes, state:str, integration:str):
    
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_base_url = authorization_base_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scope = self._get_scopes(scopes)
        self.key = os.getenv('ENCRYPTION_KEY')
        self.state = state
        self.token = self.get_token()
        self.client = WebApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=self.client, redirect_uri=self.redirect_uri, scope=self.scope)
        self.integration = integration
        
        if self.key is None:
            raise Exception('ENCRYPTION_KEY not found in environment variables')

    def _get_scopes(self, scopes) -> str:
        return scopes[0] if isinstance(scopes, tuple) else scopes
        
    def _get_authorization_url(self, **kwargs):
        print(self.oauth.__dict__)
        authorization_url, _ = self.oauth.authorization_url(self.authorization_base_url, state=self.state, **kwargs)
        return authorization_url

    def save_token(self, client_id, code):
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            # Your token exchange code
            token = self.oauth.fetch_token(self.token_url, code=code, client_secret=self.client_secret)
            print(token)
            # Store the token in the database
            store_encrypted_token(client_id, integration=self.integration, token=token, key=self.key)

    def get_token(self):
        # Retrieve decrypted token from database
        token = retrieve_decrypted_token(self.state, self.integration, self.key)
        
        # If token does not exist or is expired, return None
        if token is None or self.is_token_expired(token):
            return None

        return token
    
    def refresh_token(self):
        oauth = OAuth2Session(self.client_id, token=self.token)
        token = oauth.refresh_token(self.token_url,
                                    client_id=self.client_id,
                                    client_secret=self.client_secret)
        
        # Update the token attribute
        self.token = token

        # Store the refreshed token
        store_encrypted_token(self.client_id, self.integration, token, self.key)

    @staticmethod
    def is_token_expired(token):
        # Check if the token has expired by comparing current time with the expiry time in the token
        return datetime.utcnow().timestamp() >= token['expires_at']

    # Example usage to make an authorized request
    def request(self, method, url, **kwargs):
        
        if self.token:
            # Check token expiry
            expiry_time = self.token['expires_at']
            if datetime.now().timestamp() > expiry_time:
                # Refresh the token
                self.refresh_token()
        if self.token is None:
            raise Exception('Token is not available or expired')
        print("self.token ", self.token['access_token'])
        print(url)

        client = OAuth2Session(self.client_id, token=self.token)
        return client.request(method, url, **kwargs)
