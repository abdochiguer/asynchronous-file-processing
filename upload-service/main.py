import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from google.cloud import storage, tasks_v2
from google.cloud.tasks_v2 import Task

app = FastAPI()

# Clients GCP
storage_client = storage.Client()
tasks_client = tasks_v2.CloudTasksClient()

# Variables d’environnement
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")
UPLOAD_BUCKET = os.getenv("UPLOAD_BUCKET")
TASK_QUEUE = os.getenv("TASK_QUEUE")
PROCESSOR_URL = os.getenv("PROCESSOR_URL")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Upload vers Cloud Storage
        bucket = storage_client.bucket(UPLOAD_BUCKET)
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file.file, content_type=file.content_type)

        # Création de la tâche Cloud Tasks
        parent = tasks_client.queue_path(PROJECT_ID, REGION, TASK_QUEUE)

        payload = {
            "bucket": UPLOAD_BUCKET,
            "filename": file.filename,
            "content_type": file.content_type or "application/octet-stream"
        }

        task = Task(
            http_request={
                "http_method": tasks_v2.HttpMethod.POST,
                "url": PROCESSOR_URL,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode("utf-8")
            }
        )

        response = tasks_client.create_task(parent=parent, task=task)

        return {
            "message": "File uploaded and queued",
            "filename": file.filename,
            "task_name": response.name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "healthy"}
