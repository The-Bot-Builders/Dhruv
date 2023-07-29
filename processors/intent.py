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

from langchain.vectorstores import FAISS

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
                'answer': Intent.IndentityQA
            }, {
                'question': "What is your age?",
                'answer': Intent.IndentityQA
            }, {
                'question': "Who made you?",
                'answer': Intent.IndentityQA
            }, {
                'question': "Summarize the context",
                'answer': Intent.ContextSummary
            }, {
                'question': "Summarize the document/s",
                'answer': Intent.ContextSummary
            }, {
                'question': "Major points from the context",
                'answer': Intent.ContextSummary
            }, {
                'question': "Summarize the url/s",
                'answer': Intent.ContextSummary
            }, {
                'question': "Summarize the conversation",
                'answer': Intent.ConversationSummary
            }, {
                'question': "Highlights and lowlights from the discussion",
                'answer': Intent.ConversationSummary
            }, {
                'question': "Summarize the discussion",
                'answer': Intent.ConversationSummary
            }, {
                'question': "What is the capital of France?",
                'answer': Intent.GeneralQA
            }, {
                'question': "How to make pancakes?",
                'answer': Intent.GeneralQA
            }, {
                'question': "At what time did India gain independence?",
                'answer': Intent.GeneralQA
            }
        ]
        
        intent_selector = SemanticSimilarityExampleSelector.from_examples(
            intent_examples,
            OpenAIEmbeddings(),
            FAISS,
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


        
