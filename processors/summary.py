from processors.db import DB

from langchain.chains.summarize import load_summarize_chain
from langchain import OpenAI, PromptTemplate

from sqlalchemy import text

class Summary:

    @staticmethod
    def save_summary(client_id, thread_id, document_id, pages):
        PROMPT_TEMPLATE = """
            You are an AI Assistant. Summarize the context provided in tripple quotes in 1000 words using lists and emojis.
            Provide 5 interesting followup questions. Format your answer in Markdown.

            ```
            {text}
            ```
        """

        PROMPT = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["text"])
        chain = load_summarize_chain(
            OpenAI(), 
            chain_type="map_reduce", 
            map_prompt=PROMPT, 
            combine_prompt=PROMPT
        )
        summary = chain.run(pages)

        engine = DB.engine(client_id)
        with engine.connect() as conn:
            DB.create_summaries_table_if_not_exists(engine, "summaries")
            conn.execute(
                text("""INSERT INTO summaries (thread_id, document_id, summary) VALUES (:thread_id, :document_id, :summary)"""), 
                parameters=dict(thread_id=thread_id, document_id=document_id, summary=summary)
            )
            conn.close()

    @staticmethod
    def get_summary(client_id, thread_id):
        summaries = []
        engine = DB.engine(client_id)
        with engine.connect() as conn:
            DB.create_summaries_table_if_not_exists(engine, "summaries")
            results = conn.execute(
                text("SELECT summary FROM summaries WHERE thread_id = :thread_id"),
                parameters=dict(thread_id=thread_id)
            )
            for result in results:
                summaries.append(result[0])
            conn.close()
        
        return '\n'.join(summaries)