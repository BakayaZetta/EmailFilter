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
from fastapi import FastAPI, UploadFile, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
import logging
import tempfile
import mistral_explain
import json
import os

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

async def process_email(filename: str, email_content: bytes):
    """
    Processes an uploaded email file asynchronously.

    Args:
        filename (str): The name of the uploaded email file.
        email_content (bytes): The content of the uploaded email file.

    Returns:
        None
    """
    logger.info("Started processing email file: %s", filename)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(email_content)
        temp_file_path = temp_file.name
    email_obj = load_email(temp_file_path)
    email_raw = load_raw_email(temp_file_path)

    await analyze_email(email_obj, email_raw, db) 
    logger.info("Finished processing email file: %s", filename)

@app.post("/analyse/")
async def analyse_email(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Endpoint to analyze an email file.

    Args:
        file (UploadFile): The uploaded email file.
        background_tasks (BackgroundTasks): Background task manager to process the email file asynchronously.

    Returns:
        JSONResponse: A response indicating that the email analysis has started.
    """
    logger.info("Received request to analyze email file: %s", file.filename)
    email_content = await file.read()  # Read the file content here

    background_tasks.add_task(process_email, file.filename, email_content)  # Pass the content to the background task
    return JSONResponse(content={"message": "Processing..."}, status_code=202)

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

