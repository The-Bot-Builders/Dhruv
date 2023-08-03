import os
import hashlib
import json

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

        chat_history = ChatHistory.get_chat_history(client_id, index_md5)
        docs = Indexing.get_from_index(client_id, index_md5, text)

        system_prompt = f"""
            Your name is {os.environ.get('BOT_NAME', 'Dhurv')}.
            You are a friendly assistant. 
            You were released on Aug 23rd, 2023. 
            You don't have a gender, you are an AI assistant.
            You were made by theBotBuilders.com team.
        """

        # Get the answer
        if len(docs):
            joined_docs = '\n'.join(map(lambda doc: doc.page_content, docs))
            system_prompt += f"""
                Answer the question directly and in details using the context provided in tripple quotes. If you don't find the answer in the context, do not make anything up.
                Use lists and emojis. Format answer in slack markdown.

                ```
                {joined_docs}
                ```
            """
        else:
            system_prompt += """
                Answer the question directly and in details. Use lists and emojis.
                Format answer in slack markdown.
            """

        messages = [
            SystemMessage(content=system_prompt),
        ]

        for chat in chat_history:
            if chat['ai']:
                messages.append(AIMessage(content=chat['reply'][:30]))
            else:
                messages.append(HumanMessage(content=chat['reply']))
        

        messages.append(HumanMessage(content=text))
        ChatHistory.save_human_query(client_id, index_md5, text)

        answer = model(messages)
        answer = answer.content
        ChatHistory.save_ai_response(client_id, index_md5, answer)

        followups = []
        if len(docs):
            joined_docs = '\n'.join(map(lambda doc: doc.page_content, docs))
            system_prompt += f"""
                Here is the context in tripple quotes.

                ```
                {joined_docs}
                ```
            """
        
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Provide 5 interesting questions that can be asked from the context. Format your answer as JSON with key 'questions' which is a list of questions.")
            ]
            followup_answer = model(messages)
            try:
                followups_json = json.loads(followup_answer.content)
                followups_json = followups_json["questions"] if "questions" in followups_json else []

                for followup in followups_json:
                    followups.append(followup)
            except Exception as err:
                print(err)
        
        return (answer, followups)
            

# Used for testing
# if __name__ == "__main__":
#     answer = QAProcessor.process("What is LangChain?", "abc")
#     print(answer)