FROM python:3.12-slim AS base

# Install system dependencies & git for Git-Saga snapshotting
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY apps/sandbox-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker application source
COPY apps/sandbox-worker/src ./src
# The judged execution path resolves immutable task/cohort fixtures from
# /tests/fixtures in the container filesystem.
COPY tests/fixtures /tests/fixtures

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
