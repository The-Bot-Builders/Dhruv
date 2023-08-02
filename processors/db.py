import os

import logging
logging.basicConfig(level=logging.INFO)

import sqlalchemy
from sqlalchemy import URL, create_engine, MetaData, Table, Column, Integer, String, text

db_url = URL.create(
    drivername="postgresql+psycopg2",
    database=os.getenv("DB_DB"),
    host=os.getenv("DB_URL"),
    port=int(os.getenv("DB_PORT")),
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
)

engine = create_engine(
    db_url, 
    isolation_level='AUTOCOMMIT',
    pool_size=20, 
    max_overflow=0
)

# Used to testing
# if __name__ == "__main__":
#     db = 
