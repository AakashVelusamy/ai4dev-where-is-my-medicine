from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import SessionLocal
from services.pharmacy_service import PharmacyService
from models.medicine import Medicine
from utils.logger import logger

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/pharmacies-nearby")
async def find_pharmacies(medicine: str = Query(...), lat: float = Query(...), lon: float = Query(...), radius: int = 5, db: Session = Depends(get_db)):
    logger.info(f"Finding nearby pharmacies for medicine: {medicine} at ({lat}, {lon}) within {radius}km")
    
    # Step 1: Resolve medicine name to ID from the SQL database
    # We use fuzzy or exact match? Exact is better here if it comes from our search result
    db_medicine = db.query(Medicine).filter(Medicine.medicine_name.ilike(medicine)).first()
    
    if not db_medicine:
        # If not found in SQL DB, we can't check inventory
        return {
            "medicine": medicine,
            "pharmacies": [],
            "substitutes": [],
            "status": "not_found",
            "message": "Medicine not found in our pharmacy inventory database."
        }

    medicine_id = db_medicine.id
    service = PharmacyService(db)
    
    try:
        # Step 2: Find nearby pharmacies for original medicine
        pharmacies = await service.get_nearby_pharmacies(lat, lon, medicine_id, radius)
        
        # Step 3: If no stock, suggest substitutes
        substitutes = []
        if not pharmacies:
            substitutes = await service.get_substitutes(medicine_id)
            
        return {
            "medicine": medicine,
            "pharmacies": pharmacies,
            "substitutes": substitutes,
            "status": "in_stock" if pharmacies else "substitute_recommended",
            "message": "Suggested substitutes if no nearby stock found." if not pharmacies else "Nearby pharmacies with stock found."
        }
    except Exception as e:
        logger.error(f"Pharmacy search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
