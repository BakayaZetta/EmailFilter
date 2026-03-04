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
from fastapi import FastAPI, UploadFile, Body, Form, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import uvicorn
import logging
import tempfile
import mistral_explain
import json
import os
from datetime import datetime
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import jwt

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
SCANNER_REQUIRE_AUTH = os.getenv("SCANNER_REQUIRE_AUTH", "true").lower() in ("1", "true", "yes")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
analysis_executor = ThreadPoolExecutor(max_workers=SCANNER_WORKERS)


def _decode_bearer_token(authorization: Optional[str]) -> Dict[str, Any]:
    if not SCANNER_REQUIRE_AUTH:
        return {}

    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Scanner auth is enabled but JWT secret is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return decoded if isinstance(decoded, dict) else {}


def _normalize_auth_identity(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload or {})

    if normalized.get("userId") is None:
        fallback_user_id = (
            normalized.get("id")
            or normalized.get("user_id")
            or normalized.get("sub")
            or normalized.get("ID_Utilisateur")
            or normalized.get("ID_UTILISATEUR")
            or normalized.get("uid")
        )
        if fallback_user_id is not None:
            normalized["userId"] = fallback_user_id

    if not normalized.get("email"):
        fallback_email = (
            normalized.get("mail")
            or normalized.get("user_email")
            or normalized.get("Email")
            or normalized.get("emailAddress")
        )
        if fallback_email:
            normalized["email"] = fallback_email

    return normalized


def _is_admin_role(role_value: Any) -> bool:
    normalized_role = str(role_value or "").strip().lower()
    return normalized_role in {"admin", "super_admin", "superadmin"}

def process_email(
    request_id: str,
    filename: str,
    email_content: bytes,
    requested_user_id: Optional[int] = None,
    requested_user_email: Optional[str] = None
):
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
        asyncio.run(
            analyze_email(
                email_obj,
                email_raw,
                db,
                requested_user_id=requested_user_id,
                requested_user_email=requested_user_email
            )
        )

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
async def analyse_email(
    file: UploadFile,
    user_id: Optional[int] = Form(default=None),
    user_email: Optional[str] = Form(default=None),
    authorization: Optional[str] = Header(default=None)
):
    """
    Endpoint to analyze an email file.

    Args:
        file (UploadFile): The uploaded email file.
        background_tasks (BackgroundTasks): Background task manager to process the email file asynchronously.

    Returns:
        JSONResponse: A response indicating that the email analysis has started.
    """
    logger.info("Received request to analyze email file: %s", file.filename)
    auth_payload = _normalize_auth_identity(_decode_bearer_token(authorization))

    authenticated_user_id = auth_payload.get("userId")
    authenticated_email = auth_payload.get("email")
    effective_user_id = int(authenticated_user_id) if authenticated_user_id is not None else user_id
    effective_user_email = str(authenticated_email).strip().lower() if authenticated_email else user_email

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
        "user_id": effective_user_id,
        "user_email": effective_user_email,
        "updated_at": datetime.utcnow().isoformat()
    }

    analysis_executor.submit(
        process_email,
        request_id,
        file.filename,
        email_content,
        effective_user_id,
        effective_user_email
    )
    return JSONResponse(content={"message": "Processing...", "request_id": request_id}, status_code=202)


@app.get("/analyse/status/{request_id}")
async def get_analysis_status(request_id: str, authorization: Optional[str] = Header(default=None)):
    auth_payload = _normalize_auth_identity(_decode_bearer_token(authorization))

    job = analysis_jobs.get(request_id)
    if not job:
        return JSONResponse(content={"message": "Request not found", "status": "unknown"}, status_code=404)

    if SCANNER_REQUIRE_AUTH:
        requester_user_id = auth_payload.get("userId")
        requester_email = str(auth_payload.get("email") or "").strip().lower()
        requester_is_admin = _is_admin_role(auth_payload.get("role"))

        job_user_id = job.get("user_id")
        job_user_email = str(job.get("user_email") or "").strip().lower()
        job_has_owner = job_user_id is not None or bool(job_user_email)
        same_user = (
            (job_user_id is not None and requester_user_id is not None and str(job_user_id) == str(requester_user_id))
            or (job_user_email and requester_email and job_user_email == requester_email)
        )

        if not requester_is_admin and job_has_owner and not same_user:
            raise HTTPException(status_code=403, detail="You do not have access to this scan status")

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

