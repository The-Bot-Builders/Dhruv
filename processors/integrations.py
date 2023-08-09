
from processors.db import engine, text

TABLE_NAME = "integrations"

class NotionIntegration:

    @staticmethod
    def process(client_id, code):
        auth = base64_encode(f"{os.environ.get('NOTION_CLIENT_ID')}:{os.environ.get('NOTION_CLIENT_SECRET')}")
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
                    access_info
                ) VALUES (
                    :client_id,
                    :access_info
                )
            """
            conn.execute(
                ""
            )