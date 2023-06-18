## Running PGVector (To store embeddings in Postgres)

We need the following things, some are quite hacky to get things working:
1. We need Postgres in RDS to have version 15 or above.
2. We need to install the pg extension called vectors using:
```
CREATE EXTENSION vector;
```
3. PGVector client has the token size hardcoded, so we need to modify the site-packages with 384 wherever it says ADA_TOKEN_COUNT. This makes it difficult to use pip installation.