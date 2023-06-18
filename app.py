from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, render_template
from waitress import serve

import json
import requests

from urlextract import URLExtract

from processors.file import TempFileManager, FileProcessor
from processors.qa import QAProcessor
from processors.url import URLProcessor

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

mappings = {}

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

@app.event("message")
def message_handler(client, message, event, say):
    team_info = client.get("team_info", None)
    team_id = team_info["team"]["id"] if team_info else None
    
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

            response = requests.get(file_url, headers={'Authorization': f'Bearer {os.environ.get("SLACK_BOT_TOKEN")}'})
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

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route('/', methods=["GET"])
def index():
    return render_template('index.html')

@flask_app.route('/slack/oauth', methods=["GET"])
def slack_oauth_redirect():
    code = request.args.get('code')
    response = requests.get(
        'https://slack.com/api/oauth.v2.access?client_id={}&client_secret={}&code={}' % (
            os.environ.get("SLACK_CLIENT_ID"),
            os.environ.get("SLACK_CLIENT_SECRET"),
            code
        )
    )
    response_json = response.json()

    team_name = response_json['team']['name']
    team_id = response_json['team']['id']
    access_token = response_json['access_token']

@flask_app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return "OK"

# Start your app
if __name__ == "__main__":
    serve(flask_app, host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
