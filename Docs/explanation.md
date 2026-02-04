
This document explains the design, components, and execution flow of the asynchronous file processing system built on Google Cloud Platform.

---

Problem :
  Modern applications frequently handle large file uploads that require time-intensive processing, such as video encoding, image manipulation, or document analysis. Traditional synchronous processing approaches create poor user experiences due to long wait times, timeout issues, and system resource constraints. Organizations need a scalable solution that can handle unpredictable file upload volumes while maintaining responsive user interfaces and ensuring reliable processing completion.

Solution :
  This recipe implements a robust asynchronous file processing system using Cloud Tasks for reliable job scheduling and Cloud Storage for durable file handling. The architecture leverages Cloud Run services to process files asynchronously, with Cloud Pub/Sub providing event-driven triggers when files are uploaded. This approach ensures scalable, fault-tolerant processing that can handle varying workloads while maintaining system responsiveness and providing comprehensive monitoring capabilities.

The system is designed to:
- Accept files quickly
- Process them asynchronously
- Scale automatically
- Remain resilient to failures

---

# Main Components

Prerequisites
  - Google Cloud Project with billing enabled and appropriate permissions.
  - Google Cloud CLI (gcloud) installed and configured.
  - Docker installed for containerizing Cloud Run services.
  - Basic knowledge of Python, REST APIs, and cloud storage concepts.
  - Understanding of asynchronous programming patterns.
  - Estimated cost: $5-15 per month for moderate usage (including Cloud Storage, Cloud Tasks, Cloud Run, and Cloud Pub/Sub costs).

# Upload Service (Cloud Run)

**Role**
- Receives files from users via HTTP
- Stores uploaded files in Cloud Storage
- Creates asynchronous tasks for processing

**Why Cloud Run?**
- Auto-scaling
- No server management
- Handles HTTP traffic efficiently

**Key Responsibilities**
- Validate uploaded files
- Upload files to the upload bucket
- Create a Cloud Task pointing to the Processing Service

---

###  Cloud Storage (Upload Bucket)

**Role**
- Stores uploaded files
- Acts as a durable and scalable storage layer


---

###  Cloud Tasks

**Role**
- Manages asynchronous execution
- Calls the Processing Service in the background

**Why Cloud Tasks?**
- Guarantees task execution
- Handles retries automatically
- Controls rate limits and concurrency

**Important Note**
Cloud Tasks does **not** read from Pub/Sub.  
It **pushes HTTP requests** directly to Cloud Run.

---

###  Processing Service (Cloud Run)

**Role**
- Receives tasks from Cloud Tasks
- Reads files from Cloud Storage
- Processes files (example: image processing, validation)
- Writes results to a results bucket

**Why a separate service?**
- Isolation of responsibilities
- Independent scaling
- Better fault tolerance

---

###  Cloud Storage (Results Bucket)

**Role**
- Stores processed output files
- Keeps original and processed data separated

---

##  Execution Flow

1. A client uploads a file to the Upload Service
2. Upload Service stores the file in the upload bucket
3. Upload Service creates a task in Cloud Tasks
4. Cloud Tasks sends an HTTP request to the Processing Service
5. Processing Service downloads the file
6. Processing logic is executed
7. Results are stored in the results bucket

This flow ensures non-blocking uploads and asynchronous processing.

---

##  Asynchronization & Scalability

### What happens if multiple files are uploaded?

- Upload Service responds immediately
- Each file creates a separate task
- Tasks are queued and processed independently
- Processing Service scales automatically

### What if processing fails?

- Cloud Tasks retries automatically
- Retry behavior is configurable
- No data loss occurs

---

##  IAM

### Service Accounts

Each service uses its own **Service Account**:

- **Upload Service Account**
  - Write access to upload bucket
  - Permission to enqueue Cloud Tasks

- **Processing Service Account**
  - Read access to upload bucket
  - Write access to results bucket


---

##  Why This Architecture?

This design:
- Decouples upload and processing
- Prevents request timeouts
- Scales under load
- Is production-ready
- Follows cloud-native best practices

---

##  Testing Strategy

The system can be tested without a UI:
- Upload files using `curl`
- Monitor Cloud Tasks queue
- Check Cloud Storage buckets

This ensures the core architecture works before adding a frontend.

---

##  Future Improvements

- Add a web UI
- Add Workflow Orchestration
- Implement File Type-Specific Processing
- Add Pub/Sub fan-out for multiple processors

---

##  Conclusion

This project demonstrates a clean, scalable, and asynchronous backend architecture using Google Cloud services, suitable for real-world production workloads.
