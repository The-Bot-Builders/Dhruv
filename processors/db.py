import os

import logging
logging.basicConfig(level=logging.INFO)

from langchain.vectorstores.pgvector import PGVector

from sqlalchemy import URL, create_engine

class DB:

    @staticmethod
    def get_connection_string(client_id):
        return PGVector.connection_string_from_db_params(
            driver="psycopg2",
            database=client_id,
            host=os.getenv("DB_URL"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
        )

# Used to testing
# if __name__ == "__main__":
#     db = 
