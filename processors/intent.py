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
    ParentQA = "ParentQA"
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
                'answer': Intent.ParentQA
            }, {
                'question': "How to make pancakes?",
                'answer': Intent.ParentQA
            }, {
                'question': "At what time did India gain independence?",
                'answer': Intent.ParentQA
            }, {
                'question': "Does the document talk about X?",
                'answer': Intent.ParentQA
            }, {
                'question': "What is Y talk about in here?",
                'answer': Intent.ParentQA
            }
        ]
        
        intent_selector = SemanticSimilarityExampleSelector.from_examples(
            intent_examples,
            OpenAIEmbeddings(),
            FAISS,
            k=1
        )

        selected_intent = intent_selector.select_examples({"question": question})
        
        intent = Intent.GeneralQA if len(selected_intent) == 0 else selected_intent[0]["answer"]
        
        if intent == Intent.IndentityQA:
            return (intent, [])
        elif intent == Intent.ContextSummary:
            return (intent, [])
        elif intent == Intent.ConversationSummary:
            return (intent, [])
        else:
            index_md5 = hashlib.md5(index.encode()).hexdigest()

            embeddings = OpenAIEmbeddings()

            retriever = PGVector.from_existing_index(
                            embedding=embeddings,
                            collection_name=index_md5,
                            distance_strategy=DistanceStrategy.COSINE,
                            pre_delete_collection = False,
                            connection_string=DB.get_connection_string(client_id),
                        )

            docs = retriever.similarity_search(question, k=10)

            if len(docs):
                return (Intent.ContextualQA, docs)

            return (Intent.GeneralQA, [])


        
