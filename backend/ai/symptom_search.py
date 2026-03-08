from sentence_transformers import SentenceTransformer
from db.qdrant import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
import pandas as pd
import os
from utils.logger import logger

class SymptomSearchService:
    def __init__(self):
        self.model = None # Lazy load model on first search
        self.client = qdrant_client
        self.collection_name = "symptoms"
        logger.info(f"SymptomSearchService initialized (Connected to Qdrant Cloud: {self.collection_name})")

    def _load_model(self):
        if self.model is None:
            logger.info("Loading BAAI/bge-small-en-v1.5 model for symptom search...")
            self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            
    async def find_medicines(self, symptoms: str, top_k=5):
        self._load_model()
        logger.info(f"Symptom search query: {symptoms}")
        try:
            # Embed user query
            query_vector = self.model.encode(symptoms) # BGE model usually likes string or list
            
            # Query Qdrant Cloud using new API
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=top_k
            )
            
            results = []
            for hit in response.points:
                results.append({
                    "medicine_name": hit.payload["medicine_name"],
                    "composition": hit.payload["composition"],
                    "uses": hit.payload["uses"],
                    "side_effects": hit.payload["side_effects"],
                    "score": float(hit.score)
                })
            
            logger.info(f"Found {len(results)} matches in Qdrant.")
            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

# Initialize service globally for loading on startup
symptom_service = SymptomSearchService()
