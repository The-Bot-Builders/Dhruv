import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from .indexing import Indexing
from .chat_history import ChatHistory

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

model = ChatOpenAI(temperature=0.0)

class QAProcessor:

    @staticmethod
    def process(text, thread_ts, client_id):
        index_md5 = hashlib.md5(thread_ts.encode()).hexdigest()

        docs = Indexing.get_from_index(client_id, index_md5, text)
        chat_history = ChatHistory.get_chat_history(client_id, index_md5)

        system_prompt = f"""
            Your name is {os.environ.get('BOT_NAME')}.
            You are a friendly assistant. 
            You were released on Aug 23rd, 2023. 
            You don't have a gender, you are an AI assistant.
            You were made by theBotBuilders.com team.
        """

        if len(docs):
            joined_docs = '\n'.join(map(lambda doc: doc.page_content, docs))
            system_prompt += f"""
                Answer the question directly and in details using the context provided in tripple quotes. Use lists and emojis.
                Also ask 3 followup questions the user can ask. Format your answer in Markdown.

                ```
                {joined_docs}
                ```
            """
        else:
            system_prompt += """
                Answer the question directly and in details. Use lists and emojis.
                Also ask 3 followup questions the user can ask. Format your answer in Markdown.
            """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=text)
        ]
        answer = model(messages)
        return answer.content
            

# Used for testing
# if __name__ == "__main__":
#     answer = QAProcessor.process("What is LangChain?", "abc")
#     print(answer)