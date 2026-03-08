from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from api import search, prescription, tablet, symptoms, pharmacies
from utils.logger import logger

app = FastAPI(title="Where is my Medicine? API")

@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log the incoming request method and URL (GET / POST)
    logger.info(f"--> Incoming API Request: {request.method} {request.url.path} | Query: {request.query_params}")
    
    # Process the request
    response = await call_next(request)
    
    process_time = time.time() - start_time
    # Log the outgoing response status and time
    logger.info(f"<-- Outgoing API Response: {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.3f}s")
    
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Where is my Medicine? API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Where is my Medicine? API...")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(prescription.router, prefix="/api", tags=["Prescription"])
app.include_router(tablet.router, prefix="/api", tags=["Tablet"])
app.include_router(symptoms.router, prefix="/api", tags=["Symptoms"])
app.include_router(pharmacies.router, prefix="/api", tags=["Pharmacies"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Where is my Medicine? API"}
