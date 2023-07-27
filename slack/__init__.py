import os
import logging

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_bolt.response import BoltResponse


import json
import requests
import re

from urlextract import URLExtract

from processors.db import DB
from processors.file import TempFileManager, FileProcessor
from processors.qa import QAProcessor
from processors.url import URLProcessor

import logging
logging.basicConfig(level=logging.INFO)

stage = os.environ.get('STAGE', 'local')
app = None

if stage == 'local':
    app = App(
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        token=os.environ.get("SLACK_BOT_TOKEN")
    )
else: 
    from sqlalchemy import URL, create_engine, text
    from sqlalchemy_utils import create_database, database_exists
    from slack_bolt.oauth.oauth_settings import OAuthSettings
    from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
    from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore

    # Initializes your app with your bot token and signing secret
    url_object = URL.create(
        "postgresql+psycopg2",
        username=os.environ.get("DB_USERNAME"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_URL"),
        port=int(os.environ.get("DB_PORT")),
        database="installations",
    )

    engine = create_engine(url_object, isolation_level='AUTOCOMMIT')
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
    
    def success(args: SuccessArgs) -> BoltResponse:
        assert args.request is not None
        
        team_db_url = url_object.set(database=args.installation.team_id)
        if not database_exists(team_db_url):
            create_database(team_db_url)
            team_engine = create_engine(team_db_url)
            with team_engine.connect() as conn:
                conn.execute(text(f"CREATE EXTENSION vector;"))
            
        return BoltResponse(
            status=200,  # you can redirect users too
            body=f"Installed {os.environ.get('BOT_NAME')} successfully on {args.installation.team_name}"
        )

    def failure(args: FailureArgs) -> BoltResponse:
        assert args.request is not None
        assert args.reason is not None
        return BoltResponse(
            status=args.suggested_status_code,
            body=f"Failed to install {os.environ.get('BOT_NAME')} due to {args.reason}"
        )

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
        callback_options=CallbackOptions(success=success, failure=failure),
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

@app.event("app_mention")
def app_mention_handler(context, client, event, say):
    common_event_handler(context, client, event, say)

@app.event("message")
def im_message_handler(context, client, event, say):
    channel_type = event.get("channel_type", None) or event["channel_type"]

    if channel_type == "im":
        common_event_handler(context, client, event, say)

def common_event_handler(context, client, event, say):
    if "subtype" in event:
        return NotImplemented
    
    thread_ts = event.get("thread_ts", None) or event["ts"]

    team_id = context.get('team_id')

    has_url = False
    has_document = False
    has_conversation = False

    text = event['text']
    text = re.sub(r"<@[A-Z0-9]+>", "", text)

    # Check for URL
    urlExtrator = URLExtract()
    urls = urlExtrator.find_urls(event['text']) if "text" in event else []

    if (len(urls)):
        for idx, url in enumerate(urls):
            say(f"Checking out the link {url}. Will let you know when I am done!", thread_ts=thread_ts)

            URLProcessor.process(url, thread_ts, team_id)

            if idx == len(urls) - 1:
                if len(urls) > 1:
                    say(f"Finished reading the links. Let me summarize what I just read.", thread_ts=thread_ts)
                else:
                    say(f"Finished reading the link. Let me summarize what I just read.", thread_ts=thread_ts)
        
            text = text.replace(url, "")
            text = text.strip()

    # Check for Files
    if "files" in event:
        for idx, file in enumerate(event["files"]):
            file_url = file['url_private']
            file_type = file['filetype']

            file_name = file_url.split("/")[-1]
            say(f"Checking out the file {file_name}. Will let you know when I am done!", thread_ts=thread_ts)

            response = requests.get(file_url, headers={'Authorization': f'Bearer {context["authorize_result"]["bot_token"]}'})
            with TempFileManager(file_name) as (temp_file_path, temp_file):
                temp_file.write(response.content)
                
                processed = FileProcessor.process(file_type, temp_file_path, thread_ts, team_id)
                if processed:
                    if idx == len(event["files"]) - 1:
                        if len(event["files"]) > 1:
                            say(f"Finished reading the files. Let me summarize what I just read.", thread_ts=thread_ts)
                        else:
                            say(f"Finished reading the file. Let me summarize what I just read.", thread_ts=thread_ts)
                    
                else:
                    say(f"Sorry, I am not able to read this type of files yet!", thread_ts=thread_ts)


    # Check for General QA
    question = None
    if text:
        question = text
    else:
        question = "Summarize the content with words not less than 200 words."
     
    answer = QAProcessor.process(question, thread_ts, team_id)
    say(text=answer, thread_ts=thread_ts)



handler = SlackRequestHandler(app)