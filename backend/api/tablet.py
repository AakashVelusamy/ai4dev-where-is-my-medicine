from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from ai.ocr_engine import ocr_service
from ai.tablet_recognizer import tablet_service
from api.search import medicine_list
from rapidfuzz import process, fuzz
import re
from utils.logger import logger

router = APIRouter()

@router.post("/tablet-photo")
async def process_tablet(file: UploadFile = File(...)):
    logger.info(f"Processing tablet photo upload: {file.filename}")
    # Read file into memory (RAM buffer)
    contents = await file.read()
    
    try:
        # Step 1: Try OCR on tablet strip text
        text = await ocr_service.extract_text(contents)
        
        detected_ocr_medicines = []
        
        if text.strip():
            # Strategy A: Check matches in the whole blob
            ocr_match = process.extractOne(text, medicine_list, scorer=fuzz.partial_ratio)
            if ocr_match and ocr_match[1] > 40: # Drastically lowered from 90
                detected_ocr_medicines.append(ocr_match[0])
            
            # Strategy B: Check individual lines
            if not detected_ocr_medicines:
                lines = [l.strip() for l in re.split(r'[\n,]', text) if len(l.strip()) > 3]
                for line in lines:
                    match = process.extractOne(line, medicine_list, scorer=fuzz.partial_ratio)
                    if match and match[1] > 40: # Drastically lowered from 92
                        detected_ocr_medicines.append(match[0])
                        break

        # Step 2: Fallback to Vision Model if OCR is inconclusive
        vision_matches = []
        if not detected_ocr_medicines:
            vision_matches = await tablet_service.identify_tablet(contents)
            
        return {
            "method_used": "OCR" if detected_ocr_medicines else "Vision Model",
            "detected_medicines": list(set(detected_ocr_medicines or vision_matches)),
            "ocr_text": text if text.strip() else "No text detected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
