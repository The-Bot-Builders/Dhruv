import os
import json
import requests
import base64

from processors.db import engine, text

TABLE_NAME = "integrations"

class NotionIntegration:

    @staticmethod
    def process(client_id, code):
        auth = NotionIntegration.base64_encode(f"{os.environ.get('NOTION_CLIENT_ID')}:{os.environ.get('NOTION_CLIENT_SECRET')}")
        response = requests.post(
            url="https://api.notion.com/v1/oauth/token",
            headers={'Authorization': f'Basic {auth}'},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.environ.get("NOTION_REDIRECT_URI")
            }
        )
        with engine.connect() as conn:
            statement = f"""
                INSERT INTO {TABLE_NAME} (
                    client_id,
                    integration,
                    access_info
                ) VALUES (
                    :client_id,
                    :integration,
                    :access_info
                ) ON CONFLICT (
                    client_id,
                    integration
                ) DO UPDATE SET access_info = EXCLUDED.access_info
            """
            conn.execute(
                text(statement),
                parameters={
                    'client_id': client_id,
                    'integration': 'notion',
                    'access_info': json.dumps(response.json())
                }
            )
    
    @staticmethod
    def get_access_token(client_id):
        with engine.connect() as conn:
            statement = f"""
                SELECT access_info ->> 'access_token' as access_token FROM {TABLE_NAME} 
                WHERE client_id = :client_id AND integration = :integration
            """
            result = conn.execute(
                text(statement),
                parameters={
                    'client_id': client_id,
                    'integration': 'notion'
                }
            )
            return result.fetchone()[0]

    @staticmethod
    def base64_encode(string):
        return base64.b64encode(string.encode('ascii')).decode('ascii')

            