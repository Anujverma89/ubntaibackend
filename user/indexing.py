import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

def convert_objectid_to_str(data):
    if isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(i) for i in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data


class SystemInfoIndexer:
    def __init__(self):
        # configure from hardcoded values
        self.collection = os.getenv("QDRANT_COLLECTION")
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


    def insert(self, info: dict):
        text = " ".join(str(info.get(k, "")) for k in (
            "sys_name","kernel_type","kernel_version",
            "arch_type","hostname","timezone","user_id"
        ))
        vector = self.embedder.encode(text).tolist()

        raw_id = info.get("_id")
        clean_payload = convert_objectid_to_str(info)


        point = PointStruct(
            id=raw_id,  # UUID object
            vector=vector,
            payload=clean_payload
        )

        self.client.upsert(collection_name=self.collection, points=[point])



    def search(self, query: str, limit: int = 5):
        """
        Returns up to `limit` payloads whose embeddings are closest
        to the query text.
        """
        qv = self.embedder.encode(query).tolist()
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=qv,
            limit=limit
        )
        return [hit.payload for hit in hits]
