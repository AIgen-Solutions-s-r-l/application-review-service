# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EditViewApp Service is a FastAPI-based middleware for job application management. It interfaces with MongoDB for data storage and RabbitMQ for async message-based communication, serving as the layer between application data sources and job application targets (Skyvern applier).

## Commands

### Install Dependencies
```bash
poetry install
```

### Run Application
```bash
python app/main.py
# or with uvicorn
uvicorn app.main:app --reload --port 8006
```

### Run Tests
```bash
pytest
# run single test
pytest tests/test_consumers.py::test_career_docs_consumer_process_message_success -v
```

## Architecture

### Data Flow
1. **CareerDocs Response** → `career_docs_response_queue` → `CareerDocsConsumer` → MongoDB (`career_docs_responses` collection)
2. **User applies** → API endpoints → `GenericPublisher` → RabbitMQ → external applier service

### Background Tasks (started in `main.py` lifespan)
- `CareerDocsConsumer`: Consumes career document responses, merges with Redis-cached job data, writes to MongoDB
- `ApplicationManagerConsumer`: Handles application status notifications
- `TimedQueueRefiller`: Periodically refills the career docs queue

### Consumer/Publisher Pattern
- `BaseConsumer`: Abstract base class in `app/services/base_consumer.py`. Implementations override `get_queue_name()` and `process_message()`
- `BasePublisher`: Abstract base class in `app/services/base_publisher.py`. Implementations override `get_queue_name()`

### Key Collections (MongoDB `resumes` database)
- `career_docs_responses`: Stores user application content, keyed by `user_id` with nested `content` dict containing applications by correlation ID

### Redis Usage
- Stores original job data by correlation ID; retrieved when CareerDocs responses arrive to reconstruct complete application data

## API Endpoints (defined in `app/routers/applier_editor.py`)
- `GET /apply_content` - Fetch unsent applications (sent=false)
- `GET /pending_content` - Fetch sent/pending applications (sent=true)
- `GET /apply_content/{application_id}` - Fetch single application with full details
- `PUT /modify_application/{application_id}` - Update specific fields
- `PUT /update_application/resume_optimized/{application_id}` - Replace entire resume
- `PUT /update_application/cover_letter/{application_id}` - Replace entire cover letter
- `POST /apply_selected` - Send selected applications to applier
- `POST /apply_all` - Send all applications to applier

## Configuration

Settings in `app/core/config.py` via pydantic-settings. Key env vars:
- `MONGODB`, `RABBITMQ_URL`, `REDIS_HOST/PORT`
- `CAREER_DOCS_QUEUE`, `CAREER_DOCS_RESPONSE_QUEUE`, `APPLICATION_MANAGER_QUEUE`
- `SECRET_KEY`, `ALGORITHM` for JWT auth

## Models

- `app/models/job.py`: `JobData` - core job listing fields
- `app/models/resume.py`: Resume structure for validation
- `app/schemas/app_jobs.py`: Response models (`JobResponse`, `DetailedJobData`, `CareerDocsResponse`, etc.)
