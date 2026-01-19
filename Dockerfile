# Alibi API Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alibi/ ./alibi/
COPY *.py ./

# Create data directory
RUN mkdir -p alibi/data

# Expose API port
EXPOSE 8000

# Run API server
CMD ["python", "-m", "alibi.alibi_api"]
