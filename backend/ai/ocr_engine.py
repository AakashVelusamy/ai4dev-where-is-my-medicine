import easyocr
import numpy as np
from PIL import Image
import io

class OCRService:
    def __init__(self):
        # Initialize EasyOCR with English
        # It runs on CPU/GPU automatically based on availability
        self.reader = easyocr.Reader(['en'], gpu=False) # Setting gpu=False for stability on 3.14 for now

    async def extract_text(self, image_bytes: bytes):
        # Convert bytes to PIL Image
        img = Image.open(io.BytesIO(image_bytes))
        img_np = np.array(img)
        
        # Run EasyOCR
        # detail=0 returns only the text strings
        result = self.reader.readtext(img_np, detail=0)
        
        return " ".join(result)

ocr_service = OCRService()
