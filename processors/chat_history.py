import tiktoken
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory

from .db import engine, text

import logging
logging.basicConfig(level=logging.INFO)

TABLE_NAME = "chat_history"

class ChatHistory:

    @staticmethod
    def get_chat_history(client_id, thread_id):
        with engine.connect() as conn:
            statement = f"""
                SELECT reply, ai
                FROM {TABLE_NAME} 
                WHERE client_id = :client_id AND thread_id = :thread_id
            """
            results = conn.execute(
                text(statement), 
                parameters={
                    'client_id': client_id,
                    'thread_id': thread_id
                }
            )
            chat_history = []
            for row in results.fetchall():
                chat_history.append({
                    'reply': row[0],
                    'ai': row[1]
                })
            return chat_history

    @staticmethod
    def save_ai_response(client_id, thread_id, response):
        with engine.connect() as conn:
            statement = f"""
                INSERT INTO {TABLE_NAME}(
                    client_id,
                    thread_id,
                    reply,
                    ai
                )
                VALUES (
                    :client_id,
                    :thread_id,
                    :reply,
                    TRUE
                )
            """
            conn.execute(
                text(statement), 
                parameters={
                    'client_id': client_id,
                    'thread_id': thread_id,
                    'reply': response
                }
            )

    @staticmethod
    def save_human_query(client_id, thread_id, query):
        with engine.connect() as conn:
            statement = f"""
                INSERT INTO {TABLE_NAME}(
                    client_id,
                    thread_id,
                    reply,
                    ai
                )
                VALUES (
                    :client_id,
                    :thread_id,
                    :reply,
                    FALSE
                )
            """
            conn.execute(
                text(statement), 
                parameters={
                    'client_id': client_id,
                    'thread_id': thread_id,
                    'reply': query
                }
            )

def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(text))
    return num_tokens


def get_memory(slack_client, channel_id, thread_ts, window):
    response = slack_client.conversations_replies(channel=channel_id, ts=thread_ts)
    messages = response['messages']
    history = ChatMessageHistory()
    total_tokens = 0
    for message in messages[-window:]:
        number_of_tokens = count_tokens(message["text"])
        print("Token count:", number_of_tokens)
        total_tokens += number_of_tokens
        if "bot_id" in message:
            history.add_ai_message(message["text"])
        else:
            history.add_user_message(message["text"])
    memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        k=window,
        chat_memory=history,
        return_messages=True
    )

    print("Total tokens:", total_tokens)
    return memory
