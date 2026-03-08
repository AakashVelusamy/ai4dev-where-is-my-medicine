from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db import database
from models import medicine
from rapidfuzz import process, fuzz
import pandas as pd
from utils.logger import logger

router = APIRouter()

medicine_list = []
medicine_dict = {}

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.on_event("startup")
def load_medicines():
    global medicine_list
    global medicine_dict
    df = pd.read_csv("data/Medicine_Details.csv").fillna("")
    medicine_list = df["Medicine Name"].tolist()
    
    # Precompute dictionary for O(1) lookups of full data
    for _, row in df.iterrows():
        name = row["Medicine Name"]
        if name not in medicine_dict:
            medicine_dict[name] = {
                "medicine_name": name,
                "composition": row["Composition"],
                "uses": row["Uses"],
                "side_effects": row["Side_effects"]
            }

@router.get("/search-medicine")
async def search_medicine(q: str = Query(..., min_length=1)):
    logger.info(f"Medicine search query: {q}")
    # Perform fuzzy search using RapidFuzz
    results = process.extract(q, medicine_list, scorer=fuzz.WRatio, limit=10)
    
    # Convert matched names into full objects
    top_matches = []
    for res in results:
        if res[1] > 60:
            top_matches.append(medicine_dict[res[0]])
            
    if not top_matches:
        raise HTTPException(status_code=404, detail="No matching medicines found")
    
    return {"query": q, "results": top_matches}
