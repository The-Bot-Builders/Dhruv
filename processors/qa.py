import os
import hashlib
import json

import logging
logging.basicConfig(level=logging.INFO)

from .indexing import Indexing
from .chat_history import ChatHistory

from summarizer.sbert import SBertSummarizer

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain.docstore.document import Document

model = ChatOpenAI(temperature=0.0)
summarize = SBertSummarizer('paraphrase-MiniLM-L6-v2')

class QAProcessor:

    @staticmethod
    def process(text, thread_ts, client_id):
        text = text.strip()
        index_md5 = hashlib.md5(thread_ts.encode()).hexdigest()

        system_prompt = f"""
            Your name is {os.environ.get('BOT_NAME', 'Dhurv')}.
            You are a friendly assistant. 
            You were released on Aug 23rd, 2023. 
            You don't have a gender, you are an AI assistant.
            You were made by theBotBuilders.com team.
        """

        chat_history = ChatHistory.get_chat_history(client_id, index_md5)

        docs = None
        answer = None
        if text == "" or "summarize" in text.lower() or "summary" in text.lower():
            text = "Summarize the content. Use Lists as much possible."
            all_docs = Indexing.get_all(client_id, index_md5, text)
            joined_docs = '\n'.join(map(lambda doc: doc.page_content, all_docs))
            summary = summarize(joined_docs, ratio=0.2, num_sentences=10)
            docs = [Document(page_content=summary)]
        else:
            docs = Indexing.get_from_index(client_id, index_md5, text)
                
        if len(docs):
            joined_docs = '\n'.join(map(lambda doc: doc.page_content, docs))
            system_prompt += f"""
                Answer the question directly using the context provided in tripple quotes. If you don't find the answer in the context, do not make anything up.

                ```
                {joined_docs}
                ```
            """
        else:
            system_prompt += """
                Answer the question directly.
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

        # Followups
        followups = []
        messages = []

        if len(chat_history) == 0:
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
            else:
                system_prompt += f"""
                    Here is the question.

                    ```
                    {text}
                    ```
                """
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content="Provide 5 interesting questions that can be asked as a followup to the provided question. Format your answer as JSON with key 'questions' which is a list of questions.")
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