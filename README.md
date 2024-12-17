
# EditViewApp Service

The **EditViewApp Service** is a Python-based application designed to handle job application processes by interfacing with MongoDB for data storage and RabbitMQ for message-based communication. It acts as a middleware layer between application data sources and job application targets.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Application Workflow](#application-workflow)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Middleware Applier Service processes job application data and communicates with:

1. **MongoDB**:
   - Retrieves resumes and job data from a structured MongoDB database.
2. **RabbitMQ**:
   - Publishes job application data to a queue for further processing.
   - Consumes messages from a queue for job recommendations.

---

## Requirements

- Python 3.12.7
- RabbitMQ server
- MongoDB server
- Virtualenv

---

## Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/yourusername/middleware-applier-service.git
    cd middleware-applier-service
    ```

2. **Create a Virtual Environment**:

    ```bash
    python3.12 -m venv venv
    ```

3. **Activate the Virtual Environment**:

    - On Windows:

        ```bash
        venv\Scripts\activate
        ```

    - On macOS/Linux:

        ```bash
        source venv/bin/activate
        ```

4. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root directory with the following configuration:

```env
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
MONGODB_URL=mongodb://localhost:27017/
SERVICE_NAME=middleware_applier
APPLY_TO_JOB_QUEUE=apply_to_job_queue
JOB_TO_APPLY_QUEUE=job_to_apply_queue
```

### Key Configuration Files

- `app/core/config.py`: General configuration settings for MongoDB, RabbitMQ, and other services.
- `app/core/appliers_config.py`: Specific configurations related to job application processing.

---

## Application Workflow

1. **RabbitMQ Messaging**:
   - Publishes resumes and associated data to the `apply_to_job_queue`.
   - Retrieves job recommendations from the `job_to_apply_queue`.

2. **MongoDB Integration**:
   - Retrieves resumes and user data from the `resumes` collection.
   - Stores processed application data in a structured format.

3. **Main Services**:
   - **Applier Service** (`app/services/applier.py`):
     - Processes resumes and job data.
     - Interfaces with RabbitMQ to manage queues.

---

# APPLICATION WORKFLOW BACKEND SIDE

![AppToCareer 3](https://github.com/user-attachments/assets/bb656f1a-1151-4652-98a4-d2217abbe4cf)


# APPLICATION WORKFLOW **FRONTEND** SIDE

![Progetto senza titolo (46)](https://github.com/user-attachments/assets/19fa34ab-64b9-4be3-ade9-60d4183d8691)


## High-Level Objective

The goal is to provide users with the ability to:

1. **View a summarized list of "pending" job applications.**
2. **Edit details of a single job application if needed.**
3. **Select one or more applications to apply for, and send them for processing.**

This interaction is divided into two main sections, referred to as:

- **Red Part**: Focused on modifying individual applications.
- **Blue Part**: Allows users to select multiple applications to apply.

---

## Steps in the Communication Flow:

### Step 1: Fetch Pending Applications (Frontend → Backend)

#### User Action
The Frontend sends a `GET` request to retrieve all "pending" job applications for a specific user (user X).

#### Backend Behavior
The Backend responds with essential information about these applications. Detailed content (like career documents or generated data) is excluded to optimize performance.

#### Frontend Behavior
Displays the data as a list of cards, each summarizing a pending application.

#### Endpoint and `curl` Example

- **Endpoint**: `GET /apply_content`
- **Description**: Retrieve all pending job applications for the authenticated user.

```bash
curl -X GET "http://localhost:8006/apply_content" \
-H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### Step 2: Modify a Single Job Application (Frontend → Backend)

#### User Action
The user selects a card to edit, triggering another request to fetch detailed information for the selected job application.

#### Backend Behavior
The Backend returns the complete information for the selected application.

#### User Interaction
The Frontend allows the user to modify individual fields of the application. Once changes are made, a `PUT` request is sent to the Backend with the updated application data.

#### Endpoints and `curl` Examples

- **Fetch Detailed Application Data**
  - **Endpoint**: `GET /apply_content/{application_id}`
  - **Description**: Retrieve detailed information for a single application.

  ```bash
  curl -X GET "http://localhost:8006/apply_content/{application_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
  ```

- **Modify a Single Application**
  - **Endpoint**: `PUT /modify_application/{application_id}`
  - **Description**: Update specific fields of an application.

  ```bash
  curl -X PUT "http://localhost:8006/modify_application/{application_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
      "job_title": "Updated Job Title",
      "description": "Updated job description"
  }'
  ```

---

### Step 3: Apply for Multiple Applications (Frontend → Backend → Skyvern)

#### User Action
The user selects one or more applications to apply for.

#### Backend Behavior
The Backend retrieves the complete data for the selected applications and sends them to Skyvern for further processing (e.g., submission or validation).

#### Skyvern's Role
Finalizes the application process by processing the received data.

#### Endpoint and `curl` Example

- **Endpoint**: `POST /apply_selected`
- **Description**: Process selected applications by sending their data for further processing.

```bash
curl -X POST "http://localhost:8006/apply_selected" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '[
    "application_id_1",
    "application_id_2"
]'
```

### Optimized Process: Apply to All
The /apply_all endpoint **efficiently** handles the scenario where the user selects to apply to **all** pending jobs by sending a single document containing all applications for the authenticated user.

How It Works:

Fetch User's Data:
The endpoint retrieves the user's single document from MongoDB that contains all job applications in the content field.

Send Entire Document:
The complete document, including all applications, is sent to RabbitMQ for processing in one batch.

Optimization:
Avoids fetching and sending each application individually, reducing overhead and improving processing time.

Example curl for Apply All

```
curl -X POST "http://localhost:8006/apply_all" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json"
```

---

## Summary of Endpoints and `curl` Examples

### 1. Fetch All Pending Applications
```bash
curl -X GET "http://localhost:8006/apply_content" \
-H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Fetch Detailed Application Data
```bash
curl -X GET "http://localhost:8006/apply_content/{application_id}" \
-H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Modify a Single Application
```bash
curl -X PUT "http://localhost:8006/modify_application/{application_id}" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '{
    "job_title": "Updated Job Title",
    "description": "Updated job description"
}'
```

### 4. Apply for Selected Applications
```bash
curl -X POST "http://localhost:8006/apply_selected" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '[
    "application_id_1",
    "application_id_2"
]'
```

### 5. Apply all (opt)
```
curl -X POST "http://localhost:8006/apply_all" \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json"
```
---

## Running the Application

Run the application using the following command:

```bash
python app/main.py
```

Make sure MongoDB and RabbitMQ are running and accessible.

---

## Testing

The project includes unit and integration tests. To run tests, execute:

```bash
pytest
```

### Tests Coverage:

- **Database Tests**: Validate MongoDB interactions (`app/tests/test_db.py`).
- **RabbitMQ Communication Tests**: Test message publishing and consuming (`app/tests/test_rabbit_comm.py`).
- **Service Logic Tests**: Validate core application logic (`app/tests/test_services.py`).

---

## Folder Structure

```plaintext
middleware_applier_service/
│
├── app/
│   ├── core/               # Core application logic (config, RabbitMQ, MongoDB)
│   ├── logs/               # Example log files
│   ├── models/             # Data models (if any)
│   ├── routers/            # API endpoints (if applicable)
│   ├── services/           # Main services (job application processing)
│   ├── tests/              # Unit and integration tests
│   └── main.py             # Entry point of the application
│
├── docs/                   # Additional documentation
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker support (if applicable)
└── README.md               # Documentation
```

---

## Contributing

1. Fork the repository.
2. Create a feature branch:

    ```bash
    git checkout -b feature-branch
    ```

3. Commit your changes:

    ```bash
    git commit -am 'Add new feature'
    ```

4. Push your branch:

    ```bash
    git push origin feature-branch
    ```

5. Create a Pull Request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---
