import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from processors.db import DB
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy

from langchain.embeddings.openai import OpenAIEmbeddings

from langchain.chat_models import ChatOpenAI

from langchain.chains import ConversationalRetrievalChain

from langchain import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class QAProcessor:

    @staticmethod
    def processIndentityQA(text, thread_ts, client_id):
        chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0)

        SYSTEM_PROMPT_TEMPLATE = f"""
            Your name is {os.environ.get('BOT_NAME')}.
            You are a friendly assistant. 
            You were released on Aug 23rd, 2023. 
            You don't have a gender, you are an AI assistant.
            You were made by theBotBuilders.com team.
        """
        HUMAN_PROMPT_TEMPLATE ="{text}"
        
        system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_TEMPLATE)
        human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_PROMPT_TEMPLATE)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # get a chat completion from the formatted messages
        answer = chat(chat_prompt.format_prompt(text=text).to_messages())
        
        return answer.content

    @staticmethod
    def processGeneralQA(text, thread_ts, client_id):
        index_md5 = hashlib.md5(thread_ts.encode()).hexdigest()

        embeddings = OpenAIEmbeddings()

        retriever = PGVector.from_existing_index(
                        embedding=embeddings,
                        collection_name=index_md5,
                        distance_strategy=DistanceStrategy.COSINE,
                        pre_delete_collection = False,
                        connection_string=DB.get_connection_string(client_id),
                    ).as_retriever()

        chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0)

        chain = ConversationalRetrievalChain.from_llm(
            llm=chat,
            chain_type="map_reduce",
            retriever=retriever
        )
        result = chain({"question": text, "chat_history": []})
        return result['answer']

    @staticmethod
    def processContextSummary(text, thread_ts, client_id):
        index_md5 = hashlib.md5(thread_ts.encode()).hexdigest()

        text = "Summarize the content within 100 words. Use emojis to make the content more fun. Use bullet points. Format the answer in Slack Markdown. Also add 5 interesting questions that I can ask."
        
        embeddings = OpenAIEmbeddings()

        retriever = PGVector.from_existing_index(
                        embedding=embeddings,
                        collection_name=index_md5,
                        distance_strategy=DistanceStrategy.COSINE,
                        pre_delete_collection = False,
                        connection_string=DB.get_connection_string(client_id),
                    )

        chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0)

        docs = retriever.similarity_search(text)

        SYSTEM_PROMPT_TEMPLATE = f"""
            You are an AI Assistant. Answer the question directly and in details using the context provided in tripple quotes.
            Also ask 3 followup questions the user can ask. Format your answer in Markdown.

            ```
            {' '.join(map(lambda x: x.page_content, docs))}
            ```
        """

        HUMAN_PROMPT_TEMPLATE ="{text}"
        
        system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_TEMPLATE)
        human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_PROMPT_TEMPLATE)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # get a chat completion from the formatted messages
        answer = chat(chat_prompt.format_prompt(text=text).to_messages())
        
        return answer.content

    @staticmethod
    def processConversationSummary(text, thread_ts, team_id):
        text = "Summarize the conversation within 100 words. Format the answer with bullet points and ascii icons. Also add 5 interesting questions that I can ask."

# Used for testing
# if __name__ == "__main__":
#     answer = QAProcessor.process("What is LangChain?", "abc")
#     print(answer)