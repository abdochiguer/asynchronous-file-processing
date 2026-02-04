import os
import json
import tempfile
import time
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import storage
from PIL import Image

# App
app = FastAPI(title="File Processing Service")

# Logging
logging.basicConfig(level=logging.INFO)

# GCP Client
storage_client = storage.Client()

RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET")

# -----------------------------
# Task payload schema
# -----------------------------
class TaskPayload(BaseModel):
    bucket: str
    filename: str
    content_type: str | None = "application/octet-stream"

# -----------------------------
# Processing endpoint
# -----------------------------
@app.post("/process")
def process_file(task: TaskPayload):
    try:
        logging.info(
            f"Processing file {task.filename} from bucket {task.bucket}"
        )

        source_bucket = storage_client.bucket(task.bucket)
        source_blob = source_bucket.blob(task.filename)

        if not source_blob.exists():
            raise HTTPException(status_code=404, detail="File not found")

        with tempfile.NamedTemporaryFile() as temp_file:
            source_blob.download_to_filename(temp_file.name)

            # Decide processing
            if task.content_type.startswith("image/"):
                processed_name = process_image(
                    temp_file.name, task.filename
                )
            else:
                processed_name = process_generic_file(
                    temp_file.name, task.filename
                )

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

            metadata_blob = results_bucket.blob(
                f"{processed_name}.metadata.json"
            )
            metadata_blob.upload_from_string(
                json.dumps(metadata, indent=2)
            )

        return {
            "message": "File processed successfully",
            "metadata": metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Processing failed")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Processing logic
# -----------------------------
def process_image(file_path: str, original_filename: str) -> str:
    with Image.open(file_path) as img:
        img.thumbnail((300, 300))
        if img.mode != "RGB":
            img = img.convert("RGB")

        processed_name = f"thumb_{original_filename}"
        img.save(file_path, "JPEG", quality=85, optimize=True)
        return processed_name


def process_generic_file(file_path: str, original_filename: str) -> str:
    return f"processed_{int(time.time())}_{original_filename}"

# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health():
    return {"status": "healthy"}
