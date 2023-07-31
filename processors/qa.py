import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from .db import DB
from .indexing import Indexing
from .chat_history import ChatHistory

from langchain import OpenAI
from langchain.chat_models import ChatOpenAI

from langchain.chains import ConversationalRetrievalChain, ConversationChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT

from langchain import PromptTemplate

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class QAProcessor:

    @staticmethod
    def process(text, thread_ts, client_id):
        index_md5 = hashlib.md5(thread_ts.encode()).hexdigest()

        docs = Indexing.get_from_index(client_id, index_md5, text)
        chat_history = ChatHistory.get_chat_history(client_id, index_md5)

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        template = f"""
            Your name is {os.environ.get('BOT_NAME')}.
            You are a friendly assistant. 
            You were released on Aug 23rd, 2023. 
            You don't have a gender, you are an AI assistant.
            You were made by theBotBuilders.com team.
        """

        if len(docs):
            template += """
                Answer the question directly and in details using the context provided in tripple quotes. Use lists and emojis.
                Also ask 3 followup questions the user can ask. Format your answer in Markdown.

                ```
                {context}
                ```

                Question: {question}
                Helpful answer:
            """

            retriever = Indexing.get_retriever(client_id, index_md5)

            qa = ConversationalRetrievalChain.from_llm(
                llm=ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0),
                retriever=retriever,
                memory=memory,
                combine_docs_chain_kwargs={"prompt": PromptTemplate(input_variables=["context", "question"], template=template)}
            )
            
            result = qa({"question": text})

            return result["answer"]
        else:
            template += """
                Answer the question directly and in details. Use lists and emojis.
                Also ask 3 followup questions the user can ask. Format your answer in Markdown.
            
                Current conversation:
                {chat_history}
                Human: {input}
                AI Assistant:
            """
            PROMPT = PromptTemplate(input_variables=["chat_history", "input"], template=template)

            qa = ConversationChain(
                prompt=PROMPT,
                llm=ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0),
                memory=memory,
            )
            
            result = qa.predict(input=text)
            return result

# Used for testing
# if __name__ == "__main__":
#     answer = QAProcessor.process("What is LangChain?", "abc")
#     print(answer)