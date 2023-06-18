## To run the app
1. First get the .env file with the secrets and put it in the root of the folder.
2. Then build the image in docker with:
```
$ docker build -t tom_the_slack_bot:latest .
```
3. Then run the image in a container:
```
$ docker run -p 3000:3000 tom_the_slack_bot:latest
```
4. Then you can use ngrok to point to your local installation:
```
$ ngrok http 3000
```
5. Next you will either need the postman collection or create a slack app and point to the ngrok api


## Running PGVector (To store embeddings in Postgres)

We need the following things, some are quite hacky to get things working:
1. We need Postgres in RDS to have version 15 or above.
2. We need to install the pg extension called vectors using:
```
CREATE EXTENSION vector;
```
3. PGVector client has the token size hardcoded, so we need to modify the site-packages with 384 wherever it says ADA_TOKEN_COUNT. This makes it difficult to use pip installation.