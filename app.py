import os

from dotenv import load_dotenv, find_dotenv


env_file = '.prod.env' if os.environ.get('STAGE', 'local') == 'prod' else '.local.env'
load_dotenv(find_dotenv(filename=env_file))

import logging
logging.basicConfig(level=logging.INFO)

from slack import handler
from processors.integrations import NotionIntegration
from integrations.confluence import ConfluenceClient
from integrations.google_docs import GoogleDocsClient


from flask import Flask, request, render_template
from waitress import serve

# Initializes your app with your bot token and signing secret
flask_app = Flask(__name__)
flask_app.config['PREFFERED_URL_SCHEME'] = 'https'

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def slack_oauth_redirect():
    return handler.handle(request)

@flask_app.route("/slack/install", methods=["GET"])
def slack_install():
    return handler.handle(request)

@flask_app.route("/notion/oauth_redirect", methods=["GET"])
def notion_oauth_redirect():
    code = request.args.get('code')
    client_id = request.args.get('state')
    
    NotionIntegration.process(client_id, code)
    return "OK"

@flask_app.route("/confluence/oauth_redirect", methods=["GET"])
def confluence_oauth_redirect():
    state = request.args.get('state')
    code = request.args.get('code')
    client = ConfluenceClient(state)
    print(request)
    client.save_token(state, code)
    # confluence.process(state, code)
    return "OK"

@flask_app.route("/google/oauth_redirect", methods=["GET"])
def google_oauth_redirect():
    state = request.args.get('state')
    code = request.args.get('code')
    client = GoogleDocsClient(state)
    print(request)
    client.save_token(state, code)
    return "OK"

@flask_app.route('/', methods=["GET"])
def index():
    return render_template('index.html')

@flask_app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return "OK"

# Start your app
if __name__ == "__main__":
    print(f"Starting app with stage: {os.environ.get('STAGE', 'local')}")
    serve(flask_app, host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
