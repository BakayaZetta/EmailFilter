FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-base.txt /app/requirements-base.txt
COPY requirements-huggingface.txt /app/requirements-huggingface.txt
RUN pip install --no-cache-dir -r /app/requirements-huggingface.txt
RUN pip install --no-cache-dir -r /app/requirements-base.txt

# Copy the rest of your application code
COPY ./src /app/src

# Set the working directory
WORKDIR /app

# Command to run your application
CMD ["python", "src/main.py"]
