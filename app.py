from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from typing import Any, Dict
import uvicorn
import os

from processor import handler as process_handler

app = FastAPI(title="Doc Processor API", description="Process documents through enhanced Docling pipeline")

# Security
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header"""
    api_key = os.getenv("API_KEY", "admin")  # Default to "admin" if not set
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

class ProcessRequest(BaseModel):
    document_url: HttpUrl

class ProcessResult(BaseModel):
    result: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "message": "Doc Processor API", 
        "docs": "/docs", 
        "auth": "Required - use Authorization: Bearer <API_KEY>"
    }

@app.post("/process", response_model=ProcessResult)
async def process_document(request: ProcessRequest, api_key: str = Depends(verify_api_key)):
    """
    Process a document through the enhanced Docling pipeline.
    
    - **document_url**: URL of the document to process (PDF, etc.)
    
    Downloads the document, processes it through Docling, and returns
    the processed output along with useful metadata.
    
    Requires Authorization header with Bearer token (API key).
    """
    try:
        result = process_handler(str(request.document_url))
        return ProcessResult(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, workers=int(os.getenv("WORKERS", "1")))