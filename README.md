
# Middleware Applier Service

The **Middleware Applier Service** is a Python-based application designed to handle job application processes by interfacing with MongoDB for data storage and RabbitMQ for message-based communication. It acts as a middleware layer between application data sources and job application targets.

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

# FUTURE APPLICATION WORKFLOW

![applySequence](https://github.com/user-attachments/assets/0d43dff6-9b9f-4f1c-9059-5ec5658fcece)


High-Level Objective
   The goal is to provide users with the ability to:
   
   View a summarized list of "pending" job applications.
   Edit details of a single job application if needed.
   Select one or more applications to apply for, and send them for processing.
   This interaction is divided into two main sections, referred to as:

Red Part: Focused on modifying individual applications.
Blue Part: Allows users to select multiple applications to apply.

Steps in the Communication Flow:

Step 1: Fetch Pending Applications (Frontend → Backend)
   Request: The Frontend sends a GET request to the Backend to retrieve all "pending" job applications for a specific user (user X).
   Response: The Backend responds with essential information about these applications. Notably, detailed content (like career documents or generated data) is excluded to optimize performance.
   Frontend Behavior: Displays the data as a list of cards, each summarizing a pending application.
   
Step 2: Modify a Single Job Application (Frontend → Backend)
   User Action: The user selects a card to edit, triggering another request to fetch detailed information for the selected job application.
   Request: The Frontend sends a GET request to the Backend for all data associated with the selected application.
   Response: The Backend returns the complete information for the selected application.
   User Interaction: The Frontend allows the user to modify individual fields of the application.
   Request (PUT): Once changes are made, the Frontend sends a PUT request to the Backend with the updated application data.
   Response: The Backend performs the necessary changes and confirms the update.

Step 3: Apply for Multiple Applications (Frontend → Backend → Skyvern)
   User Action: The user selects one or more applications to apply for.
   Request (POST): The Frontend sends a POST request to the Backend with the IDs of the selected applications.
   Backend Behavior:
   Retrieves the complete data for the selected applications.
   Sends the applications to Skyvern for further processing (e.g., submission or validation).
   Skyvern's Role: Finalizes the application process by processing the received data.

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
