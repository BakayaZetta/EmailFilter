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
        curl -X POST "http://0.0.0.0:6969/analyse" -F "file=@path_to_email_file.eml"
        Replace `path_to_email_file.eml` with the path to the email file you want to analyze.
"""

from database import Database 
from analysis.mail_analyzer import load_email, analyze_email, load_raw_email
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTasks
import uvicorn
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

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

@app.post("/analyse")
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
    return JSONResponse(content={"message": "Email analysis started."}, status_code=202)

# Add a health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)

