import os

import re
import urllib.parse
import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


import requests


from urlextract import URLExtract

from processors.db import engine
from processors.file import TempFileManager, FileProcessor
from processors.qa import QAProcessor
from processors.url import URLProcessor

from integrations.confluence import ConfluenceClient
from integrations.google_docs import GoogleDocsClient

from .slack_formatting import convert_markdown_to_slack

logging.basicConfig(level=logging.INFO)

app = None
stage = os.environ.get('STAGE', 'local')
bot_name = os.environ.get('BOT_NAME', 'Dhruv')

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
def update_home_tab(context, client, event, logger):
    team_id = context.get('team_id')
    notion_redirect_uri_encoded = urllib.parse.quote(os.environ.get('NOTION_REDIRECT_URI'))
    confluence_client = ConfluenceClient(team_id)
    confluence_authorization_url = confluence_client.get_authorization_url()
    google_docs_client = GoogleDocsClient(team_id)
    google_docs_authorization_url = google_docs_client.get_authorization_url()

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
                            "text": f"Hello User! :wave: \nWelcome to *{bot_name}*, your one-stop solution for managing integrations. We help you connect and streamline your workflow."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"With *{bot_name}*, you can integrate various services seamlessly, making your daily tasks more efficient and connected."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Connect to your *Notion* workspace to bring your notes and documents under one roof."
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                            "type": "plain_text",
                            "text": "Connect to Notion"
                            },
                            "url": f"https://api.notion.com/v1/oauth/authorize?state={team_id}&client_id=4ccd95a3-d835-4e46-9bb0-2a74d425d350&response_type=code&owner=user&redirect_uri={notion_redirect_uri_encoded}",
                            "value": "add_notion",
                            "action_id": "add_integration"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Integrate *Confluence* workspace to manage and collaborate on your team projects."
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                            "type": "plain_text",
                            "text": "Connect to Confluence"
                            },
                            "url": f"{confluence_authorization_url}",
                            "value": "add_confluence",
                            "action_id": "add_integration"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Link your *Google Docs* workspace to easily access and share your files across platforms."
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                            "type": "plain_text",
                            "text": "Connect to Google Docs"
                            },
                            "url": f"{google_docs_authorization_url}",
                            "value": "add_google_docs",
                            "action_id": "actionId-0"
                        }
                    }
                ]})
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

@app.action("button")
def ask_followup_button_click(ack, context, client, action, say):
    ack()

    (text, thread_id) = action['value'].split("<->")
    
    team_id = context.get('team_id')
    bot_token = context["authorize_result"]["bot_token"]

    say(blocks=[{
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"<@{context['user_id']}> asked '{text}'"}
    }], text='', thread_ts=thread_id)
    
    common_message_handler(text, action, thread_id, team_id, bot_token, say, client)

@app.action("add_integration")
def add_integration(ack, context, client, action, say):
    ack()

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
    
    thread_id = event.get("thread_ts", None) or event["ts"]
    team_id = context.get('team_id')
    bot_token = context["authorize_result"]["bot_token"]

    # Message formatting
    text = event['text']
    text = re.sub(r"<@[A-Z0-9]+>", "", text)

    common_message_handler(text, event, thread_id, team_id, bot_token, say, client)

def common_message_handler(text, meta, thread_id, team_id, bot_token, say, client):

    # Check for URL
    processURLs(text, meta, thread_id, team_id, bot_token, say, client)

    # Check for Files
    processFiles(text, meta, thread_id, team_id, bot_token, say, client)
    
    (answer, followups) = QAProcessor.process(text, thread_id, team_id)

    if answer:
        say(blocks=[{
            "type": "section",
            "text": {"type": "mrkdwn", "text": convert_markdown_to_slack(answer)}
        }], text=answer, thread_ts=thread_id)
    
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
                        "value": followup + "<->" + thread_id,
                        "action_id": "button"
                    }
                }
            )
        say(blocks=blocks, text=answer, thread_ts=thread_id)

def processURLs(text, meta, thread_id, team_id, bot_token, say, client):
    urlExtrator = URLExtract()
    urls = urlExtrator.find_urls(text)

    if (len(urls)):
        for idx, url in enumerate(urls):
            say(f"Checking out the link {url}. Will let you know when I am done!", thread_ts=thread_id)

            try:
                URLProcessor.process(url, thread_id, team_id)
            except Exception as e:
                say(f"Sorry, failed to read the URL. Getting this this error: {e}", thread_ts=thread_id)
        
            text = text.replace(url, "")
            text = text.strip()
        
        if text != "":
            return
        
        if len(urls) > 1:
            say("Finished reading the links. Let me summarize what I just read.", thread_ts=thread_id)
        else:
            say("Finished reading the link. Let me summarize what I just read.", thread_ts=thread_id)

def processFiles(text, meta, thread_id, team_id, bot_token, say, client):
    if "files" not in meta:
        return
    files = meta['files']

    for idx, file in enumerate(files):
        file_url = file['url_private']
        file_type = file['filetype']

        file_name = file_url.split("/")[-1]
        say(f"Checking out the file {file_name}. Will let you know when I am done!", thread_ts=thread_id)

        response = requests.get(file_url, headers={'Authorization': f'Bearer {bot_token}'}, timeout=30)
        with TempFileManager(file_name) as (temp_file_path, temp_file):
            temp_file.write(response.content)
            
            processed = FileProcessor.process(file_type, temp_file_path, thread_id, team_id)
            if not processed:
                say("Sorry, I am not able to read this type of files yet!", thread_ts=thread_id)
        
        if text != "":
            return

        if len(files) > 1:
            say("Finished reading the files.", thread_ts=thread_id)
        else:
            say("Finished reading the file.", thread_ts=thread_id)
            text = text.strip()
        if not text:
            say("Let me summarize the content. Please be patient.", thread_ts=thread_id)

handler = SlackRequestHandler(app)