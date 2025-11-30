<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB">
  <img src="https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<h1 align="center">
  <br>
  Application Review Service
  <br>
</h1>

<h4 align="center">AI-powered job application orchestration layer — where human oversight meets automation.</h4>

<p align="center">
  <a href="#-the-vision">Vision</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-deployment">Deploy</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/coverage-85%25-green?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/async-100%25-blueviolet?style=flat-square" alt="Async">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
</p>

---

## 🎯 The Vision

In a world where job seekers send hundreds of applications, we believe in **quality over quantity**.

This service is the intelligent middleware that sits between AI-generated career documents and automated job submission — giving users the power to **review, refine, and approve** before a single application goes out.

> *"Automation without oversight is just spam. We're building thoughtful automation."*

---

## 🏗 Architecture

```mermaid
flowchart TB
    subgraph External["☁️ External Services"]
        CD[("🤖 CareerDocs AI")]
        SK[("⚡ Skyvern")]
        PR[("🔌 ATS Providers")]
    end

    subgraph Core["🎯 Application Review Service"]
        direction TB
        API["🌐 FastAPI Gateway"]

        subgraph Consumers["📥 Message Consumers"]
            CDC["CareerDocs Consumer"]
            AMC["App Manager Consumer"]
        end

        subgraph Publishers["📤 Message Publishers"]
            CDP["CareerDocs Publisher"]
            GP["Generic Publisher"]
        end

        TQR["⏰ Timed Queue Refiller"]
    end

    subgraph Data["💾 Data Layer"]
        MDB[("🍃 MongoDB")]
        RD[("⚡ Redis")]
        RMQ[("🐰 RabbitMQ")]
    end

    subgraph Users["👥 Clients"]
        FE["💻 Frontend App"]
        MOB["📱 Mobile App"]
    end

    FE & MOB --> API
    API --> MDB
    API --> GP

    CDP --> RMQ
    GP --> RMQ

    RMQ --> CDC
    RMQ --> AMC

    CDC --> MDB
    CDC --> RD

    TQR --> CDP
    AMC --> CDP

    RMQ <--> CD
    RMQ --> SK
    RMQ --> PR

    RD <--> CDP

    style Core fill:#1a1a2e,stroke:#16213e,color:#fff
    style Data fill:#0f3460,stroke:#16213e,color:#fff
    style External fill:#533483,stroke:#16213e,color:#fff
    style Users fill:#e94560,stroke:#16213e,color:#fff
```

### Data Flow

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant API as 🌐 API
    participant MDB as 🍃 MongoDB
    participant RMQ as 🐰 RabbitMQ
    participant AI as 🤖 CareerDocs AI
    participant RD as ⚡ Redis
    participant APP as ⚡ Appliers

    Note over U,APP: Phase 1: AI Document Generation
    U->>API: Submit job listings
    API->>RD: Store job data (correlation_id)
    API->>RMQ: Queue for AI processing
    RMQ->>AI: Process jobs
    AI->>RMQ: Return optimized CV + Cover Letter
    RMQ->>API: Consume response
    API->>RD: Retrieve original job data
    API->>MDB: Store complete application

    Note over U,APP: Phase 2: Human Review
    U->>API: GET /apply_content
    API->>MDB: Fetch pending applications
    API-->>U: Display for review
    U->>API: Edit resume/cover letter
    API->>MDB: Update application

    Note over U,APP: Phase 3: Automated Submission
    U->>API: POST /apply_selected
    API->>MDB: Mark as sent
    API->>RMQ: Queue for submission
    RMQ->>APP: Submit to job portals
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 Smart Queue Management
- Auto-refilling job queues
- Configurable batch sizes
- Retry logic with exponential backoff
- Dead letter handling for failed jobs

### 🛡️ Enterprise Security
- JWT authentication
- Environment-based secret management
- Production-safe defaults
- Input validation with Pydantic

</td>
<td width="50%">

### ⚡ High Performance
- 100% async architecture
- Non-blocking Redis operations
- Connection pooling
- Horizontal scalability ready

### 🔌 Pluggable Appliers
- Skyvern integration (browser automation)
- Native ATS provider support
- Easy to add new appliers
- Portal-based routing

</td>
</tr>
</table>

### Supported Job Portals

| Portal | Status | Portal | Status |
|--------|--------|--------|--------|
| Workday | ✅ Native | Lever | ✅ Native |
| Greenhouse | ✅ Native | Workable | ✅ Native |
| SmartRecruiters | ✅ Native | BambooHR | ✅ Native |
| Dice | ✅ Native | BreezyHR | ✅ Native |
| ApplyToJob | ✅ Native | InfoJobs | ✅ Native |
| Others | 🤖 Skyvern | | |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required services
docker run -d --name mongodb -p 27017:27017 mongo:latest
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
docker run -d --name redis -p 6379:6379 redis:latest
```

### Installation

```bash
# Clone the repository
git clone https://github.com/AIgen-Solutions-s-r-l/application-review-service.git
cd application-review-service

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the service
python app/main.py
```

### Environment Configuration

```env
# Core
ENVIRONMENT=development
SECRET_KEY=your-super-secret-key-here

# MongoDB
MONGODB=mongodb://localhost:27017

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Queues
CAREER_DOCS_QUEUE=career_docs_queue
CAREER_DOCS_RESPONSE_QUEUE=career_docs_response_queue

# Appliers (feature flags)
ENABLE_SKYVERN_APPLIER=false
ENABLE_PROVIDERS_APPLIER=true
```

---

## 📡 API Reference

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/apply_content` | List pending applications |
| `GET` | `/pending_content` | List sent/processing applications |
| `GET` | `/apply_content/{id}` | Get application details |
| `PUT` | `/modify_application/{id}` | Update specific fields |
| `PUT` | `/update_application/resume_optimized/{id}` | Replace entire resume |
| `PUT` | `/update_application/cover_letter/{id}` | Replace entire cover letter |
| `POST` | `/apply_selected` | Submit selected applications |
| `POST` | `/apply_all` | Submit all pending applications |
| `GET` | `/health` | Service health check |

### Example Requests

<details>
<summary><b>📋 Get Pending Applications</b></summary>

```bash
curl -X GET "http://localhost:8006/apply_content" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response:**
```json
{
  "applications": [
    {
      "id": "uuid-1234",
      "company": "TechCorp",
      "position": "Senior Engineer",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```
</details>

<details>
<summary><b>✏️ Update Resume</b></summary>

```bash
curl -X PUT "http://localhost:8006/update_application/resume_optimized/{application_id}" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {
      "header": {
        "personal_information": {
          "name": "John",
          "surname": "Doe",
          "email": "john@example.com"
        }
      },
      "body": {
        "experience_details": {...},
        "education_details": {...}
      }
    }
  }'
```
</details>

<details>
<summary><b>🚀 Submit Applications</b></summary>

```bash
curl -X POST "http://localhost:8006/apply_selected" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '["uuid-1234", "uuid-5678"]'
```
</details>

---

## 🐳 Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8006:8006"
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - MONGODB=mongodb://mongo:27017
      - REDIS_HOST=redis
      - RABBITMQ_URL=amqp://rabbitmq:5672/
    depends_on:
      - mongo
      - redis
      - rabbitmq

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine

  rabbitmq:
    image: rabbitmq:3-management

volumes:
  mongo_data:
```

### Kubernetes Ready

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: application-review-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: application-review-service
  template:
    spec:
      containers:
      - name: app
        image: application-review-service:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_consumers.py -v
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_consumers.py        # Message consumer tests
├── test_publisher.py        # Publisher tests
├── test_appliers_config.py  # Applier routing tests
├── test_database_writer.py  # DB operations tests
├── test_generic_publisher.py
├── test_redis_client.py
└── test_timed_queue_refiller.py
```

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8006/health
```

### Metrics (Datadog Integration)

The service includes built-in Datadog logging integration. Set these environment variables:

```env
DD_API_KEY=your-datadog-api-key
LOGLEVEL_DATADOG=ERROR
```

---

## 🗺️ Roadmap

- [ ] WebSocket support for real-time updates
- [ ] GraphQL API layer
- [ ] Multi-tenant architecture
- [ ] Application analytics dashboard
- [ ] AI-powered application scoring
- [ ] Batch optimization algorithms

---

## 🤝 Contributing

We love contributions! Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

```bash
# Fork, clone, and create a branch
git checkout -b feature/amazing-feature

# Make your changes and test
pytest

# Commit with conventional commits
git commit -m "feat: add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

---

## 📄 License

MIT © [AIgen Solutions](https://github.com/AIgen-Solutions-s-r-l)

---

<p align="center">
  <sub>Built with ❤️ by humans who believe AI should augment, not replace, human judgment.</sub>
</p>

<p align="center">
  <a href="https://github.com/AIgen-Solutions-s-r-l">
    <img src="https://img.shields.io/badge/GitHub-AIgen--Solutions-181717?style=for-the-badge&logo=github" alt="GitHub">
  </a>
</p>
