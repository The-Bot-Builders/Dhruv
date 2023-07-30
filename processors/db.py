import os

import logging
logging.basicConfig(level=logging.INFO)

from langchain.vectorstores.pgvector import PGVector

import sqlalchemy
from sqlalchemy import URL, create_engine, MetaData, Table, Column, Integer, String

engines = {

}

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

    @staticmethod
    def engine(database):
        if database not in engines:
            engine = create_engine(DB.get_connection_string(database), isolation_level='AUTOCOMMIT')
            engines[database] = engine

        return engines[database]

    @staticmethod
    def create_summaries_table_if_not_exists(engine, table):
        if not sqlalchemy.inspect(engine).has_table(table):  # If table don't exist, Create.
            metadata = MetaData()
            # Create a table with the appropriate Columns
            Table(table, metadata,
                Column('id', Integer, primary_key=True, nullable=False), 
                Column('thread_id', String),
                Column('document_id', String),
                Column('summary', String),
            )
            # Implement the creation
            metadata.create_all(engine)

# Used to testing
# if __name__ == "__main__":
#     db = 
