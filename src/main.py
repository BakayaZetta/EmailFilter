"""
This script analyzes emails for SPF, DKIM, and DMARC status and saves the results to the database.

Functions:
    main: Main function to analyze emails and save results to the database.

Usage:
    Run this script directly to start the email analysis.
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
    """Process the uploaded email file."""
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
    """Endpoint to analyze an email file."""
    logger.info("Received request to analyze email file: %s", file.filename)
    email_content = await file.read()  # Read the file content here
    background_tasks.add_task(process_email, file.filename, email_content)  # Pass the content to the background task
    return JSONResponse(content={"message": "Email analysis started."}, status_code=202)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)

