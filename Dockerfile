# Build stage
FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.source=https://github.com/AIHawk-Startup/edit_confirm_applications_pending_service

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml /app/

# Set working directory
WORKDIR /app

# Configure poetry to not create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false
# Install dependencies
RUN poetry install --no-root --only main

COPY ./app /app/app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8003

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]