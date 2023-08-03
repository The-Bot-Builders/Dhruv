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

from processors.db import engine
from processors.file import TempFileManager, FileProcessor
from processors.qa import QAProcessor
from processors.url import URLProcessor

from .slack_formatting import convert_markdown_to_slack

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
    from sqlalchemy_utils import create_database, database_exists
    from slack_bolt.oauth.oauth_settings import OAuthSettings
    from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
    from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore

    # Initializes your app with your bot token and signing secret
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
        state_store=state_store
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

    # Slack related
    if event.get('subtype', None) != None and event['subtype'] not in ["file_share"]:
        return NotImplemented
    
    thread_ts = event.get("thread_ts", None) or event["ts"]
    team_id = context.get('team_id')
    bot_token = context["authorize_result"]["bot_token"]

    # conversations_in_thread = client.conversations_replies(
    #     channel=event['channel'],
    #     ts=thread_ts,
    # )
    # print('\n'.join(list(map(lambda x: x['text'], conversations_in_thread['messages']))))

    # Message formatting
    text = event['text']
    text = re.sub(r"<@[A-Z0-9]+>", "", text)

    # Check for URL
    processURLs(text, thread_ts, team_id, bot_token, say)

    # Check for Files
    if "files" in event:
        processFiles(text, event['files'], thread_ts, team_id, bot_token, say)
    
    (answer, followups) = QAProcessor.process(text, thread_ts, team_id)

    if answer:
        say(blocks=[{
            "type": "section",
            "text": {"type": "mrkdwn", "text": convert_markdown_to_slack(answer)}
        }], text=answer, thread_ts=thread_ts)
    
    if len(followups):
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Interesting followup questions you can ask me to learn more:"
            }
        }]
        for idx, followup in enumerate(followups):
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": followup
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"Ask {os.environ.get('BOT_NAME', 'Dhurv')}"
                        },
                        "value": followup,
                        "action_id": "button"
                    }
                }
            )
        say(blocks=blocks, text=answer, thread_ts=thread_ts)

def processURLs(text, thread_ts, team_id, bot_token, say):
    urlExtrator = URLExtract()
    urls = urlExtrator.find_urls(text)

    if (len(urls)):
        for idx, url in enumerate(urls):
            say(f"Checking out the link {url}. Will let you know when I am done!", thread_ts=thread_ts)

            URLProcessor.process(url, thread_ts, team_id)
        
            text = text.replace(url, "")
            text = text.strip()
        
        if text != "":
            return
        
        if len(urls) > 1:
            say(f"Finished reading the links. Let me summarize what I just read.", thread_ts=thread_ts)
        else:
            say(f"Finished reading the link. Let me summarize what I just read.", thread_ts=thread_ts)

def processFiles(text, files, thread_ts, team_id, bot_token, say):
    for idx, file in enumerate(files):
        file_url = file['url_private']
        file_type = file['filetype']

        file_name = file_url.split("/")[-1]
        say(f"Checking out the file {file_name}. Will let you know when I am done!", thread_ts=thread_ts)

        response = requests.get(file_url, headers={'Authorization': f'Bearer {bot_token}'})
        with TempFileManager(file_name) as (temp_file_path, temp_file):
            temp_file.write(response.content)
            
            processed = FileProcessor.process(file_type, temp_file_path, thread_ts, team_id)
            if not processed:
                say(f"Sorry, I am not able to read this type of files yet!", thread_ts=thread_ts)
        
        if text != "":
            return

        if len(files) > 1:
            say(f"Finished reading the files. Let me summarize what I just read.", thread_ts=thread_ts)
        else:
            say(f"Finished reading the file. Let me summarize what I just read.", thread_ts=thread_ts)

handler = SlackRequestHandler(app)