FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY atomic/notification/notification.py ./notification.py

# Expose the port the app runs on
EXPOSE 5002

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "notification.py"]