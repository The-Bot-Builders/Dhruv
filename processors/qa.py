import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from processors.db import CONNECTION_STRING
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy

from langchain.embeddings.huggingface import HuggingFaceEmbeddings

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from langchain.prompts import PromptTemplate

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_DESCRIPTION = f"Your name is {os.environ.get('BOT_NAME')}, and you are a smart software engineer. You are encouraging and cheerful. "
TEMPLATE = BOT_DESCRIPTION + """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:"""

class QAProcessor:

    @staticmethod
    def process(question, index):
        index_md5 = hashlib.md5(index.encode()).hexdigest()

        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

        retriever = PGVector.from_existing_index(
                        embedding=embeddings,
                        collection_name=index_md5,
                        distance_strategy=DistanceStrategy.COSINE,
                        pre_delete_collection = False,
                        connection_string=CONNECTION_STRING,
                    ).as_retriever()

        chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.0)

        chain = RetrievalQA.from_chain_type(
            llm=chat,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template=TEMPLATE,
                    input_variables=["context", "question"]
                )
            }
        )
        answer = chain.run(question)
        return answer

# Used for testing
# if __name__ == "__main__":
#     answer = QAProcessor.process("What is LangChain?", "abc")
#     print(answer)