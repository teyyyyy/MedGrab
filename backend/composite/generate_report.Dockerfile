FROM python:3.9-slim
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY composite/ .

# Expose port and set environment
EXPOSE 5005
ENV PYTHONUNBUFFERED=1

CMD ["python", "generate_report.py"]