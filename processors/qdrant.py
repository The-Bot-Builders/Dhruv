import os

from qdrant_client import QdrantClient

url = f"https://{os.environ.get('QDRANT_URL', 'localhost')}:{os.environ.get('QDRANT_PORT', '6333')}"

client = QdrantClient(
    os.environ.get("QDRANT_URL", "localhost"), 
    port=int(os.environ.get("QDRANT_PORT", "6333"))
)
