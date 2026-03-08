from fastapi import APIRouter, HTTPException, Query
from ai.symptom_search import symptom_service
from utils.logger import logger

router = APIRouter()

@router.get("/symptom-search")
async def process_symptoms(symptoms: str = Query(..., min_length=1)):
    logger.info(f"Symptom search query: {symptoms}")
    try:
        results = await symptom_service.find_medicines(symptoms)
        
        if not results:
            raise HTTPException(status_code=404, detail="No matching medicines for symptoms")
        
        return {
            "query": symptoms,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
