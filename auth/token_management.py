import psycopg2
from cryptography.fernet import Fernet
import json
from processors.db import engine, text

OUTH_TOKEN_TABLE_NAME = "oauth_tokens"

# Function to store encrypted token
def store_encrypted_token(client_id: str, integration: str, token: any, key: str):
    cipher_suite = Fernet(key)
    token_json = json.dumps(token)
    encrypted_token = cipher_suite.encrypt(token_json.encode())
    print("encrypted_token: ", encrypted_token)

    # Database connection
    with engine.connect() as conn:
         
        # Insert or update the token in the database
        statement = f"""
            INSERT INTO {OUTH_TOKEN_TABLE_NAME} (
                client_id,
                integration,
                encrypted_token
            ) VALUES (
                :client_id,
                :integration,
                :encrypted_token
            ) ON CONFLICT (
                        client_id,
                        integration
                    ) DO UPDATE SET encrypted_token = EXCLUDED.encrypted_token
                """
        conn.execute(
            text(statement),
            parameters={
                'client_id': client_id,
                'integration': integration,
                'encrypted_token': encrypted_token
            }
        )


# Function to retrieve decrypted token
def retrieve_decrypted_token(client_id, integration, key):
    # Database connection
    with engine.connect() as conn:
        statement = f"""
                SELECT encrypted_token FROM {OUTH_TOKEN_TABLE_NAME} 
                WHERE client_id = :client_id AND integration = :integration
            """
        result = conn.execute(
            text(statement),
            parameters={
                'client_id': client_id,
                'integration': integration
            }
        )
        row = result.fetchone()
        if row is None:
            return None

        encrypted_token = bytes(row[0])
        print("encrypted_token: ", encrypted_token)
        cipher_suite = Fernet(key)
        decrypted_token_json = cipher_suite.decrypt(encrypted_token).decode()
        decrypted_token = json.loads(decrypted_token_json)

        return decrypted_token
