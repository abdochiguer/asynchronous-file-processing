import os
import json
import tempfile
import time
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import storage, tasks_v2
from PIL import Image

# --------------------------------------------------
# App
# --------------------------------------------------
app = FastAPI(title="File Processing Service")

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)

# --------------------------------------------------
# GCP Clients
# --------------------------------------------------
storage_client = storage.Client()
tasks_client = tasks_v2.CloudTasksClient()

# --------------------------------------------------
# Environment variables
# --------------------------------------------------
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET")
DLQ_SERVICE_URL = os.environ.get("DLQ_SERVICE_URL")
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = "europe-west1"
DLQ_QUEUE = "my-dlq-queue"

# --------------------------------------------------
# Task payload schema
# --------------------------------------------------
class TaskPayload(BaseModel):
    bucket: str
    filename: str
    content_type: str | None = "application/octet-stream"


# --------------------------------------------------
# Send task to DLQ
# --------------------------------------------------
def send_to_dlq(payload: dict):
    try:
        parent = tasks_client.queue_path(PROJECT_ID, LOCATION, DLQ_QUEUE)

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": DLQ_SERVICE_URL,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
            }
        }

        tasks_client.create_task(parent=parent, task=task)
        logging.info("Task sent to DLQ successfully")

    except Exception as e:
        logging.exception("Failed to send task to DLQ")
        logging.error(str(e))


# --------------------------------------------------
# Processing endpoint
# --------------------------------------------------
@app.post("/process")
def process_file(task: TaskPayload):
    try:
        logging.info(f"Processing file {task.filename} from bucket {task.bucket}")

        source_bucket = storage_client.bucket(task.bucket)
        source_blob = source_bucket.blob(task.filename)

        if not source_blob.exists():
            raise HTTPException(status_code=404, detail="File not found")

        with tempfile.NamedTemporaryFile() as temp_file:
            source_blob.download_to_filename(temp_file.name)

            # Processing decision
            if task.content_type.startswith("image/"):
                processed_name = process_image(temp_file.name, task.filename)
            else:
                processed_name = process_generic_file(temp_file.name, task.filename)

            # Upload result
            results_bucket = storage_client.bucket(RESULTS_BUCKET)
            results_blob = results_bucket.blob(processed_name)
            results_blob.upload_from_filename(temp_file.name)

            metadata = {
                "original_filename": task.filename,
                "processed_filename": processed_name,
                "content_type": task.content_type,
                "status": "completed",
                "processed_at": time.time(),
            }

            metadata_blob = results_bucket.blob(f"{processed_name}.metadata.json")
            metadata_blob.upload_from_string(json.dumps(metadata, indent=2))

        return {
            "message": "File processed successfully",
            "metadata": metadata,
        }

    except HTTPException:
        raise

    except Exception as e:
        logging.exception("Processing failed")

        # Send to DLQ
        send_to_dlq({
            "error": str(e),
            "file": task.filename,
            "bucket": task.bucket,
            "time": time.time()
        })

        # IMPORTANT: return 500 so Cloud Tasks knows it failed
        raise HTTPException(status_code=500, detail="Processing failed")


# --------------------------------------------------
# Image processing
# --------------------------------------------------
def process_image(file_path: str, original_filename: str) -> str:
    with Image.open(file_path) as img:
        img.thumbnail((300, 300))
        if img.mode != "RGB":
            img = img.convert("RGB")

        processed_name = f"thumb_{original_filename}"
        img.save(file_path, "JPEG", quality=85, optimize=True)
        return processed_name


# --------------------------------------------------
# Generic file processing
# --------------------------------------------------
def process_generic_file(file_path: str, original_filename: str) -> str:
    return f"processed_{int(time.time())}_{original_filename}"


# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "healthy"}
