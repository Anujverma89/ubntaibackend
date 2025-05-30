import os 
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, VectorParams, Distance

class ErrorIndexer:
    def __init__(self):
        self.collection = "error_database"
        self.client = QdrantClient(
            url= os.getenv("QDRANT_URI"), 
            api_key= os.getenv("QDRANT_API"),
        )

        # load a lightweight embedder
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # ensure our target collection exists with the right vector size
        if not self.client.collection_exists(collection_name=self.collection):
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedder.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )