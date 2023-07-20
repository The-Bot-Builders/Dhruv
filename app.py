import os

from dotenv import load_dotenv, find_dotenv

env_file = '.prod.env' if os.environ.get('STAGE') == 'prod' else '.local.env'
load_dotenv(find_dotenv(filename=env_file))

from slack import handler

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

@flask_app.route('/', methods=["GET"])
def index():
    return render_template('index.html')

@flask_app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return "OK"

# Start your app
if __name__ == "__main__":
    serve(flask_app, host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
