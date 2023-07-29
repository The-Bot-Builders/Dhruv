import os
import hashlib

import logging
logging.basicConfig(level=logging.INFO)

from processors.db import DB
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy

from langchain.embeddings.openai import OpenAIEmbeddings

from langchain.llms import OpenAI

from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector

from langchain.vectorstores import Chroma

class Intent:

    IndentityQA = "IdentityQA"
    GeneralQA = "GeneralQA"
    ContextualQA = "ContextualQA"
    ConversationSummary = "ConversationSummary"
    ContextSummary = "ContextSummary"


class IntentProcessor:

    @staticmethod
    def process(question, index, client_id):
        index_md5 = hashlib.md5(index.encode()).hexdigest()

        intent_examples = [
            {
                'question': "What is your name?",
                'answer': 'IdentityQA'
            }, {
                'question': "What is your age?",
                'answer': 'IdentityQA'
            }, {
                'question': "Who made you?",
                'answer': 'IdentityQA'
            }, {
                'question': "Summarize the context",
                'answer': 'ContextualSummary'
            }, {
                'question': "Summarize the document/s",
                'answer': 'ContextualSummary'
            }, {
                'question': "Major points from the context",
                'answer': 'ContextualSummary'
            }, {
                'question': "Summarize the url/s",
                'answer': 'ContextualSummary'
            }, {
                'question': "Summarize the conversation",
                'answer': 'ConversationSummary'
            }, {
                'question': "Highlights and lowlights from the discussion",
                'answer': "ConversationSummary"
            }, {
            'question': "Summarize the discussion",
            'answer': "ConversationSummary"
            }, {
                'question': "What is the capital of France?",
                'answer': "QA"
            }, {
                'question': "How to make pancakes?",
                'answer': "QA"
            }, {
                'question': "At what time did India gain independence?",
                'answer': "QA"
            }
        ]
        
        intent_selector = SemanticSimilarityExampleSelector.from_examples(
            intent_examples,
            OpenAIEmbeddings(),
            Chroma,
            k=1
        )

        selected_intent = intent_selector.select_examples({"question": question})
        
        intent = 'GeneralQA'

        if len(selected_intent) != 0 and selected_intent[0]["answer"] in [
            Intent.IndentityQA,
            Intent.ContextSummary,
            Intent.ConversationSummary
        ]:
            intent = selected_intent[0]["answer"]
        
        return intent


        
