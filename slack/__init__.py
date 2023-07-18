import os

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore

from sqlalchemy import URL, create_engine

import json
import requests

from urlextract import URLExtract

from processors.file import TempFileManager, FileProcessor
from processors.qa import QAProcessor
from processors.url import URLProcessor

# Initializes your app with your bot token and signing secret
url_object = URL.create(
    "postgresql+psycopg2",
    username=os.environ.get("DB_USERNAME"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_URL"),
    port=int(os.environ.get("DB_PORT")),
    database="installations",
)

engine = create_engine(url_object)
installation_store = SQLAlchemyInstallationStore(
    client_id=os.environ.get("SLACK_CLIENT_ID"),
    engine=engine
)
installation_store.create_tables()
state_store = SQLAlchemyOAuthStateStore(
    expiration_seconds=600,
    engine=engine
)
state_store.metadata.create_all(engine)
oauth_settings = OAuthSettings(
    client_id=os.environ.get("SLACK_CLIENT_ID"),
    client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
    scopes=[
        "app_mentions:read", 
        "channels:history",
        "chat:write",
        "files:read",
        "im:history",
        "im:read",
        "im:write",
        "groups:history"
    ],
    installation_store=installation_store,
    state_store=state_store,
)

app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    oauth_settings=oauth_settings,
)

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "callback_id": "home_view",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Welcome to your _App's Home_*: :tada:"
                        }
                    },
                    {
                        "type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Click me!"
                                }
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

@app.event("app_mentions")
def app_mentions_handler(context, client, message, event, say):
    common_message_handler(context, client, message, event, say)

@app.event("message.app_home")
def im_message_handler(context, client, message, event, say):
    common_message_handler(context, client, message, event, say)

def common_message_handler(context, client, message, event, say):
    thread_ts = event.get("thread_ts", None) or event["ts"]

    urlExtrator = URLExtract()
    urls = urlExtrator.find_urls(message['text']) if "text" in message else []
    
    if (len(urls)):
        for url in urls:
            say(f"Learning the content from the URL {url}...", thread_ts=thread_ts)

            URLProcessor.process(url, thread_ts)
            say(f"Done learning the content", thread_ts=thread_ts)
    elif "files" in message:
        for file in message["files"]:
            file_url = file['url_private']
            file_type = file['filetype']

            file_name = file_url.split("/")[-1]
            say(f"Learning the content of the file named {file_name}...", thread_ts=thread_ts)

            response = requests.get(file_url, headers={'Authorization': f'Bearer {context["authorize_result"]["bot_token"]}'})
            with TempFileManager(file_name) as (temp_file_path, temp_file):
                temp_file.write(response.content)
                
                processed = FileProcessor.process(file_type, temp_file_path, thread_ts)
                if processed:
                    say(f"Done learning the content", thread_ts=thread_ts)
                else:
                    say(f"Sorry, I am not able to read this type of files yet!", thread_ts=thread_ts)
    elif "subtype" in message:
        return NotImplemented
    else:
        answer = QAProcessor.process(message['text'], thread_ts)
        say(text=answer, thread_ts=thread_ts)


handler = SlackRequestHandler(app)