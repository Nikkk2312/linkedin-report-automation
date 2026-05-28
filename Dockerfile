FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    libreoffice-impress \
    libreoffice-common \
    fonts-liberation \
    sqlite3 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install n8n globally
RUN npm install -g n8n@latest

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ src/
COPY scripts/ scripts/
COPY templates/ templates/
COPY assets/ assets/
COPY docs/ docs/
COPY app.py .
COPY run.py .
COPY workflow.json .
COPY VERSION .

# Create output, config, and data directories
RUN mkdir -p output config data static

# Environment defaults
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV N8N_PORT=5678
ENV NODES_EXCLUDE="[]"
ENV NODE_FUNCTION_ALLOW_BUILTIN="fs,path,child_process"
ENV N8N_BLOCK_ENV_ACCESS_IN_NODE=false
ENV N8N_RUNNERS_TASK_TIMEOUT=900
ENV DATA_STORE_PATH=data/reports.db
ENV REPORT_ARCHIVE_DAYS=30

EXPOSE 5000 5678

# Volumes for persistent data
VOLUME ["/app/output", "/app/data", "/app/config"]

# Start the Flask dashboard
CMD ["python", "app.py"]
