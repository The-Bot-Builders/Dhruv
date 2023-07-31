import tiktoken
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory

class ChatHistory:

    @staticmethod
    def get_chat_history(client_id, thread_id):
        pass

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
