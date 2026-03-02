FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    tcpdump \
    net-tools \
    iputils-ping \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY servers.txt .

# Create output directories
RUN mkdir -p results plots models logs

# Make scripts executable
RUN chmod +x run_experiment.py iperf_client.py data_collector.py visualization.py ml_model.py

# Default command
CMD ["python3", "run_experiment.py", "--help"]
