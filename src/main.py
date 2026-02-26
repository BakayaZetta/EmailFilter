"""
This script provides a FastAPI-based web service for analyzing emails for SPF, DKIM, and DMARC status.

Modules:
    - database: Handles database interactions.
    - analysis.mail_analyzer: Contains functions for loading and analyzing email files.

Functions:
    - process_email: Processes an uploaded email file asynchronously.
    - analyse_email: FastAPI endpoint to analyze an email file.
    - health_check: FastAPI endpoint for health checks.

Usage:
    Run this script directly to start the FastAPI server.
    Example curl command to analyze an email file:
        curl -X POST "http://0.0.0.0:6969/analyse/" -F "file=@path_to_email_file.eml"
        Replace `path_to_email_file.eml` with the path to the email file you want to analyze.
"""

from database import Database 
from analysis.mail_analyzer import load_email, analyze_email, load_raw_email
from fastapi import FastAPI, UploadFile, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
import logging
import tempfile
import mistral_explain
import json
import os
from datetime import datetime
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS configuration to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
analysis_jobs: Dict[str, Dict[str, Any]] = {}


def _get_positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        logger.warning("Invalid value for %s=%s. Using default %s.", name, value, default)
        return default


MAX_EMAIL_SIZE_MB = _get_positive_int_env("MAX_EMAIL_SIZE_MB", 25)
MAX_EMAIL_SIZE_BYTES = MAX_EMAIL_SIZE_MB * 1024 * 1024
SCANNER_WORKERS = _get_positive_int_env("SCANNER_WORKERS", 1)
analysis_executor = ThreadPoolExecutor(max_workers=SCANNER_WORKERS)

def process_email(request_id: str, filename: str, email_content: bytes):
    """
    Processes an uploaded email file asynchronously.

    Args:
        filename (str): The name of the uploaded email file.
        email_content (bytes): The content of the uploaded email file.

    Returns:
        None
    """
    analysis_jobs[request_id] = {
        "status": "processing",
        "filename": filename,
        "updated_at": datetime.utcnow().isoformat()
    }
    logger.info("Started processing email file: %s", filename)
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(email_content)
            temp_file_path = temp_file.name
        email_obj = load_email(temp_file_path)
        email_raw = load_raw_email(temp_file_path)

        import asyncio
        asyncio.run(analyze_email(email_obj, email_raw, db))

        analysis_jobs[request_id] = {
            "status": "finished",
            "filename": filename,
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info("Finished processing email file: %s", filename)
    except Exception as error:
        analysis_jobs[request_id] = {
            "status": "failed",
            "filename": filename,
            "error": str(error),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.exception("Failed processing email file: %s", filename)
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/analyse/")
async def analyse_email(file: UploadFile):
    """
    Endpoint to analyze an email file.

    Args:
        file (UploadFile): The uploaded email file.
        background_tasks (BackgroundTasks): Background task manager to process the email file asynchronously.

    Returns:
        JSONResponse: A response indicating that the email analysis has started.
    """
    logger.info("Received request to analyze email file: %s", file.filename)
    email_content = await file.read(MAX_EMAIL_SIZE_BYTES + 1)
    if len(email_content) > MAX_EMAIL_SIZE_BYTES:
        logger.warning(
            "Rejected oversized email file: %s (%s bytes > %s bytes)",
            file.filename,
            len(email_content),
            MAX_EMAIL_SIZE_BYTES,
        )
        return JSONResponse(
            content={
                "message": f"Email too large. Maximum allowed size is {MAX_EMAIL_SIZE_MB}MB.",
            },
            status_code=413,
        )

    request_id = str(uuid4())
    analysis_jobs[request_id] = {
        "status": "queued",
        "filename": file.filename,
        "updated_at": datetime.utcnow().isoformat()
    }

    analysis_executor.submit(process_email, request_id, file.filename, email_content)
    return JSONResponse(content={"message": "Processing...", "request_id": request_id}, status_code=202)


@app.get("/analyse/status/{request_id}")
async def get_analysis_status(request_id: str):
    job = analysis_jobs.get(request_id)
    if not job:
        return JSONResponse(content={"message": "Request not found", "status": "unknown"}, status_code=404)
    return job

# Add a health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/mistral/")
async def ai_answer(file_to_explain):
    return mistral_explain.answer(file_to_explain)

@app.post("/analyse/mistral/")
async def generate_mistral_explanation(data: Dict[str, Any]):
    """
    Endpoint to generate a Mistral explanation for an email
    
    Args:
        data: Data containing the email ID and its complete details
    """
    try:
        email_id = data.get("emailId")
        email_data = data.get("emailData")
        
        if not email_id:
            return {"error": "Missing email ID", "status": "error"}
            
        # Use the detailed email data if available
        if email_data:
            print(f"Complete data received for email ID {email_id}")
            
            # Generate explanation from the detailed data
            explanation = mistral_explain.generate_explanation(email_data)
            
            return {
                "explanation": explanation,
                "status": "success"
            }
        else:
            # Fallback: retrieve data from the database
            print(f"No detailed data received for email ID {email_id}, retrieving from database")
            email_data = {"id": email_id, "message": "Data not available"}
            
            explanation = "I did not receive enough information to analyze this email. Please verify the system configuration."
            
            return {
                "explanation": explanation,
                "status": "limited"
            }
    except Exception as e:
        print(f"Error generating explanation: {str(e)}")
        return {
            "explanation": f"An error occurred during analysis: {str(e)}",
            "status": "error"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)

