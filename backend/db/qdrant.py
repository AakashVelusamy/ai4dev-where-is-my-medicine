from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

# Central Qdrant Client for Cloud or Local storage
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if qdrant_url and qdrant_api_key:
    # Use Cloud Qdrant
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60)
else:
    # Fallback to local
    qdrant_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "qdrant_db")
    qdrant_client = QdrantClient(path=qdrant_path)

def get_qdrant_client():
    return qdrant_client
