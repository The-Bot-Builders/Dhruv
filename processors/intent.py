import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from langchain.embeddings.openai import OpenAIEmbeddings

from langchain.llms import OpenAI

from langchain.prompts import PromptTemplate

class IntentProcessor:

    @staticmethod
    def process(question):
        # model = OpenAI(model_name='gpt-3.5-turbo', temperature=0.0)

        return "GeneralQA"


        
