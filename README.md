
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
