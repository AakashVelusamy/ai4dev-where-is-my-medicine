import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
from db.qdrant import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
import pandas as pd
import os
from utils.logger import logger

class TabletRecognizerService:
    def __init__(self):
        self.model = None
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.client = qdrant_client
        self.collection_name = "tablets"
        logger.info(f"TabletRecognizerService initialized (Connected to Qdrant Cloud: {self.collection_name})")

    def _load_model(self):
        if self.model is None:
            logger.info("Loading Vision model for tablet recognition...")
            self.model = models.resnet50(pretrained=True)
            self.feature_extractor = nn.Sequential(*list(self.model.children())[:-1])
            self.feature_extractor.eval()

    async def get_embedding(self, image_bytes: bytes):
        # Convert bytes to PIL Image
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_tensor = self.preprocess(img).unsqueeze(0)
        
        # Extract features
        with torch.no_grad():
            features = self.feature_extractor(img_tensor)
            embedding = features.squeeze().numpy()
            
        return embedding

    async def identify_tablet(self, image_bytes: bytes):
        self._load_model()
        logger.info("Identifying tablet image...")
        try:
            embedding = await self.get_embedding(image_bytes)
            
            # Query Qdrant Cloud using new API
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=embedding.tolist(),
                limit=5
            )
            
            results = []
            if response.points:
                # Always take at least the top match if available
                results.append(response.points[0].payload["medicine_name"])
                
                # For the rest, use a very low threshold
                for hit in response.points[1:]:
                    if hit.score > 0.2:
                        results.append(hit.payload["medicine_name"])
            
            if not results:
                logger.warning("No high-confidence tablet vision match found.")
                
            return results
        except Exception as e:
            logger.error(f"Tablet identification failed: {str(e)}")
            return []

tablet_service = TabletRecognizerService()
