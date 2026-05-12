# Dockerfile for AVA - Academic Authenticity Validator

# Use Python 3.10 slim as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV STREAMLIT_SERVER_PORT 8501

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for uploads and reports
RUN mkdir -p uploads reports

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Make start script executable
RUN chmod +x start.sh

# Start the application
CMD ["./start.sh"]
