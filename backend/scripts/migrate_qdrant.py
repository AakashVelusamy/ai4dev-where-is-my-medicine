import pandas as pd
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
import requests
import warnings
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Distance, VectorParams, PointStruct
from db.qdrant import qdrant_client
from utils.logger import logger
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress annoying requests/urllib3 version warnings
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*charset_normalizer.*")

def migrate_symptoms():
    collection_name = "symptoms"
    medicine_data_path = "data/Medicine_Details.csv"
    
    if not os.path.exists(medicine_data_path):
        logger.error(f"Data file not found at {medicine_data_path}")
        return

    # Check if collection exists
    collections = qdrant_client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if exists:
        logger.info(f"Removing existing collection '{collection_name}' for clean cloud migration.")
        qdrant_client.delete_collection(collection_name)
    
    logger.info(f"Starting migration to Qdrant Cloud collection: {collection_name}")
    
    # Load model and data
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    df = pd.read_csv(medicine_data_path).fillna("")
    
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    
    # Generate points lazily for streaming
    def yield_symptom_points():
        embeddings = model.encode(df["Uses"].tolist(), show_progress_bar=True)
        for idx, emb in enumerate(embeddings):
            yield PointStruct(
                id=idx,
                vector=emb.tolist(),
                payload={
                    "medicine_name": df.iloc[idx]["Medicine Name"],
                    "composition": df.iloc[idx]["Composition"],
                    "uses": df.iloc[idx]["Uses"],
                    "side_effects": df.iloc[idx]["Side_effects"]
                }
            )

    # Stream points to Qdrant in batches
    qdrant_client.upload_points(
        collection_name=collection_name,
        points=yield_symptom_points(),
        batch_size=100,
        parallel=2,
        wait=True
    )

    logger.info(f"Symptom migration complete.")

def process_image(idx, row, preprocess, feature_extractor):
    img_url = row["Image URL"]
    med_name = row["Medicine Name"]
    
    if not img_url or "gumlet.io" not in img_url:
        return None
        
    try:
        # Faster download with stream=True and slightly tighter timeout
        response = requests.get(img_url, timeout=3, stream=True)
        if response.status_code != 200:
            return None
            
        img = Image.open(io.BytesIO(response.content)).convert('RGB')
        img_tensor = preprocess(img).unsqueeze(0)
        
        with torch.no_grad():
            feat = feature_extractor(img_tensor).squeeze().numpy()
        
        return PointStruct(
            id=idx,
            vector=feat.tolist(),
            payload={"medicine_name": med_name}
        )
    except Exception:
        return None

def migrate_tablets():
    collection_name = "tablets"
    medicine_data_path = "data/Medicine_Details.csv"
    
    # Check if collection exists
    collections = qdrant_client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if exists:
        logger.info(f"Removing existing collection '{collection_name}'")
        qdrant_client.delete_collection(collection_name)
    
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=2048, distance=Distance.COSINE),
    )

    # Load Vision Model
    model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
    feature_extractor = nn.Sequential(*list(model.children())[:-1])
    feature_extractor.eval()
    
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    df = pd.read_csv(medicine_data_path).fillna("")
    logger.info(f"Streaming visual vectors for {len(df)} medicines using multi-threaded consumer...")

    # Generator for streaming points with internal parallel processing
    def yield_tablet_points_parallel():
        max_workers = 15 # Higher workers for network-bound tasks
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We process in small chunks of futures to maintain streaming behavior
            # and avoid overloading memory
            chunk_size = 100 
            for i in range(0, len(df), chunk_size):
                chunk_df = df.iloc[i:i+chunk_size]
                futures = {executor.submit(process_image, idx, row, preprocess, feature_extractor): idx 
                           for idx, row in chunk_df.iterrows()}
                
                count = 0
                for future in as_completed(futures):
                    point = future.result()
                    if point:
                        yield point
                        count += 1
                
                logger.info(f"Chunk starting at {i}: Yielded {count}/{len(chunk_df)} valid visual points")

    # Qdrant client's internal batch streaming
    qdrant_client.upload_points(
        collection_name=collection_name,
        points=yield_tablet_points_parallel(),
        batch_size=50, # Size of batch sent to Qdrant
        parallel=2,    # Parallel uploads to Qdrant Cloud
        wait=True
    )

    logger.info(f"Full tablet migration complete via parallel streaming.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "tablets":
        migrate_tablets()
    else:
        migrate_symptoms()
