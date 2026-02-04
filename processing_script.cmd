cd processing-service

# Build and deploy processing service
gcloud builds submit --tag gcr.io/${PROJECT_ID}/processing-service .

gcloud run deploy processing-service \
    --image gcr.io/${PROJECT_ID}/processing-service \
    --region ${REGION} \
    --platform managed \
    --no-allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --concurrency 50 \
    --max-instances 20 \
    --set-env-vars PROJECT_ID=${PROJECT_ID},RESULTS_BUCKET=${RESULTS_BUCKET}

# Get processing service URL
PROCESSING_SERVICE_URL=$(gcloud run services describe processing-service \
    --region ${REGION} \
    --format "value(status.url)")

cd . .

echo "✅ Cloud Run services deployed successfully"
echo "Upload Service URL: ${UPLOAD_SERVICE_URL}"
echo "Processing Service URL: ${PROCESSING_SERVICE_URL}"