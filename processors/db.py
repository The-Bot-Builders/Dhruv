import os

from langchain.vectorstores.pgvector import PGVector

CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg2",
    database="rd-embeddings",
    host=os.getenv("DB_URL"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
)

# Used to testing
# if __name__ == "__main__":
#     db = 
