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
import time
import threading
from datetime import datetime
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pika
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()


def _parse_allowed_origins() -> list[str]:
    raw_origins = os.getenv("SCANNER_CORS_ALLOWED_ORIGINS", "")
    parsed = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
    if parsed:
        return parsed
    return [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
    ]

# CORS configuration to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
SCANNER_WORKERS = _get_positive_int_env("SCANNER_WORKERS", 3)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
SCAN_QUEUE_NAME = os.getenv("SCAN_QUEUE_NAME", "scan_jobs")
RABBITMQ_ENABLED = os.getenv("RABBITMQ_ENABLED", "true").lower() in ("1", "true", "yes")
RABBITMQ_RETRY_SECONDS = _get_positive_int_env("RABBITMQ_RETRY_SECONDS", 5)
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


def _stage_uploaded_email(email_content: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as temp_file:
        temp_file.write(email_content)
        return temp_file.name


def _enqueue_scan_job(job_payload: Dict[str, Any]) -> bool:
    if not RABBITMQ_ENABLED:
        return False

    connection = None
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=SCAN_QUEUE_NAME, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=SCAN_QUEUE_NAME,
            body=json.dumps(job_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        return True
    except Exception as error:
        logger.warning("Unable to enqueue scan job via RabbitMQ, falling back to local executor: %s", error)
        return False
    finally:
        if connection and connection.is_open:
            connection.close()


def process_email(
    request_id: str,
    filename: str,
    requested_user_id: int | None = None,
    requested_user_email: str | None = None,
    email_content: bytes | None = None,
    staged_file_path: str | None = None
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
    source_file_path = staged_file_path
    local_db = None
    try:
        if source_file_path is None and email_content is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as temp_file:
                temp_file.write(email_content)
                temp_file_path = temp_file.name
                source_file_path = temp_file_path

        if source_file_path is None:
            raise ValueError("No email payload provided for analysis")

        email_obj = load_email(source_file_path)
        email_raw = load_raw_email(source_file_path)

        local_db = Database()

        import asyncio
        analysis_succeeded = asyncio.run(
            analyze_email(
                email_obj,
                email_raw,
                local_db,
                requested_user_id=requested_user_id,
                requested_user_email=requested_user_email
            )
        )

        analysis_jobs[request_id] = {
            "status": "finished" if analysis_succeeded else "failed",
            "filename": filename,
            "error": None if analysis_succeeded else "analysis_failed_or_timed_out",
            "updated_at": datetime.utcnow().isoformat()
        }
        if analysis_succeeded:
            logger.info("Finished processing email file: %s", filename)
        else:
            logger.warning("Email analysis finished with failure/timeout: %s", filename)
    except Exception as error:
        analysis_jobs[request_id] = {
            "status": "failed",
            "filename": filename,
            "error": str(error),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.exception("Failed processing email file: %s", filename)
    finally:
        if local_db is not None:
            local_db.close()
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if staged_file_path and os.path.exists(staged_file_path):
            os.remove(staged_file_path)


def _consume_scan_jobs_forever(worker_index: int):
    worker_name = f"scan-worker-{worker_index}"
    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            channel.queue_declare(queue=SCAN_QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            logger.info("%s connected to RabbitMQ queue '%s'", worker_name, SCAN_QUEUE_NAME)

            for method_frame, _, body in channel.consume(SCAN_QUEUE_NAME):
                if method_frame is None:
                    continue

                try:
                    payload = json.loads(body.decode('utf-8'))
                    process_email(
                        request_id=payload.get('request_id'),
                        filename=payload.get('filename'),
                        requested_user_id=payload.get('user_id'),
                        requested_user_email=payload.get('user_email'),
                        staged_file_path=payload.get('staged_file_path')
                    )
                except Exception as error:
                    request_id = None
                    try:
                        request_id = payload.get('request_id')
                    except Exception:
                        pass
                    if request_id and request_id in analysis_jobs:
                        analysis_jobs[request_id] = {
                            "status": "failed",
                            "filename": payload.get('filename') if isinstance(payload, dict) else None,
                            "error": str(error),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    logger.exception("%s failed to process queued scan: %s", worker_name, error)
                finally:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        except Exception as error:
            logger.warning("%s RabbitMQ consumer disconnected: %s", worker_name, error)
            time.sleep(RABBITMQ_RETRY_SECONDS)
        finally:
            if connection and connection.is_open:
                connection.close()


def _start_rabbitmq_consumers_if_enabled():
    if not RABBITMQ_ENABLED:
        logger.info("RabbitMQ queueing disabled; using local executor with %s workers", SCANNER_WORKERS)
        return

    for worker_index in range(1, SCANNER_WORKERS + 1):
        worker_thread = threading.Thread(
            target=_consume_scan_jobs_forever,
            args=(worker_index,),
            daemon=True,
            name=f"scan-worker-{worker_index}"
        )
        worker_thread.start()

    logger.info("Started %s RabbitMQ scan workers", SCANNER_WORKERS)


_start_rabbitmq_consumers_if_enabled()

@app.post("/analyse/")
async def analyse_email(
    file: UploadFile,
    user_id: int | None = Form(default=None),
    user_email: str | None = Form(default=None),
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

    staged_file_path = _stage_uploaded_email(email_content)
    queued_via_rabbitmq = _enqueue_scan_job({
        "request_id": request_id,
        "filename": file.filename,
        "user_id": effective_user_id,
        "user_email": effective_user_email,
        "staged_file_path": staged_file_path
    })

    if not queued_via_rabbitmq:
        analysis_executor.submit(
            process_email,
            request_id,
            file.filename,
            effective_user_id,
            effective_user_email,
            None,
            staged_file_path
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

        # Backward compatibility: older jobs may not have owner metadata.
        # If request is authenticated and job has no owner, allow access.
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

