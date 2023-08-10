import os
import requests
import base64

from slack import handler
from processors.integrations import NotionIntegration

from flask import Flask, request, render_template
from waitress import serve

import logging
logging.basicConfig(level=logging.INFO)

# Initializes your app with your bot token and signing secret
flask_app = Flask(__name__)

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
