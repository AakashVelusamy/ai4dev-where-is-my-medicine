from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ai.ocr_engine import ocr_service
from api.search import medicine_list
from rapidfuzz import process, fuzz
import re
from utils.logger import logger

router = APIRouter()

@router.post("/prescription")
async def process_prescription(file: UploadFile = File(...)):
    logger.info(f"Processing prescription upload: {file.filename}")
    # Read file into memory (RAM buffer)
    contents = await file.read()
    
    try:
        # Step 1: Extract text using OCR
        text = await ocr_service.extract_text(contents)

        # Step 2: Extract medicine candidates using a more robust heuristic
        # Split text into lines and blocks to check each segment
        lines = [line.strip() for line in re.split(r'[\n,]', text) if len(line.strip()) > 3]
        
        found_medicines = []
        seen_names = set()

        for line in lines:
            # Lowering threshold significantly from 85 to 30
            match = process.extractOne(line, medicine_list, scorer=fuzz.partial_ratio)
            if match and match[1] > 30:
                if match[0] not in seen_names:
                    found_medicines.append(match[0])
                    seen_names.add(match[0])

        # If no line matches, try individual word matching but more carefully
        if not found_medicines:
            words = re.findall(r'\b[A-Za-z]{4,}\b', text)
            for word in set(words):
                # Lowering threshold from 90 to 40
                match = process.extractOne(word, medicine_list, scorer=fuzz.ratio)
                if match and match[1] > 40:
                    if match[0] not in seen_names:
                        found_medicines.append(match[0])
                        seen_names.add(match[0])
        
        # Absolute fallback: if STILL nothing, just take the best partial match of the whole text
        if not found_medicines and text.strip():
            match = process.extractOne(text, medicine_list, scorer=fuzz.partial_ratio)
            if match:
                found_medicines.append(match[0])
        
        return {
            "method_used": "OCR-NER",
            "extracted_text": text,
            "detected_medicines": found_medicines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
