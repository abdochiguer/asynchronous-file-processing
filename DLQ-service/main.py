from fastapi import FastAPI, Request
import logging
from google.cloud import tasks_v2
import os

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Use environment variables instead of hardcoded values
PROJECT_ID = os.getenv("PROJECT_ID", "YOUR_PROJECT_ID")
LOCATION = "europe-west1"
QUEUE_NAME = "file-processing-queue"

client = tasks_v2.CloudTasksClient()
parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)

@app.post("/dlq")
async def process_dlq(request: Request):
    payload = await request.json()
    task_name = payload.get("taskName", "unknown")
    error = payload.get("error", "no error info")
    
    logging.error(f"DLQ task received: {task_name}")
    logging.error(f"Error details: {error}")
    
    return {"status": "DLQ processed"}

# Add a health check endpoint (Cloud Run uses this)
@app.get("/")
async def health_check():
    return {"status": "healthy"}