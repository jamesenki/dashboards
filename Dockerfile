# Use CUDA-enabled base image for GPU support (can be changed to CPU-only if needed)
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    cmake \
    curl \
    git \
    wget \
    libblas-dev \
    liblapack-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    gfortran \
    llvm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GPU support
ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    PYTHONUNBUFFERED=1

# Install TimescaleDB client and MongoDB for AI data stores
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories for model storage and data
RUN mkdir -p /app/models /app/data /app/ml_experiments

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install lightweight LLM support - used only when GPU is available
ARG INSTALL_LLM=false
RUN if [ "$INSTALL_LLM" = "true" ]; then \
      pip install --no-cache-dir llama-cpp-python==0.2.32 \
      sentence-transformers==2.3.1 \
      langchain==0.0.239 \
      ctransformers==0.2.27; \
    fi

# Set up model directory as a volume for easier model management
VOLUME /app/models

# Copy ML test data for TDD approach
COPY testdata /app/testdata

# Copy the rest of the application
COPY . .

# Create directory for test reports
RUN mkdir -p /app/test_reports

# Create script to run tests with TDD approach
RUN echo '#!/bin/bash\npytest src/tests/ml -v --junitxml=/app/test_reports/ml_test_results.xml "$@"' > /app/run_ml_tests.sh && \
    chmod +x /app/run_ml_tests.sh

# Expose ports for the API and ML monitoring
EXPOSE 8000 8080 6006

# Healthcheck to verify the service is running correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
