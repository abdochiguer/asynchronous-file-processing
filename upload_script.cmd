# Build and deploy upload service
cd upload-service

gcloud builds submit --tag gcr.io/${PROJECT_ID}/upload-service .

gcloud run deploy upload-service \
    --image gcr.io/${PROJECT_ID}/upload-service \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 100 \
    --max-instances 10 \
    --set-env-vars PROJECT_ID=${PROJECT_ID},REGION=${REGION},UPLOAD_BUCKET=${UPLOAD_BUCKET},TASK_QUEUE=${TASK_QUEUE}

# Get upload service URL
UPLOAD_SERVICE_URL=$(gcloud run services describe upload-service \
    --region ${REGION} \
    --format "value(status.url)")