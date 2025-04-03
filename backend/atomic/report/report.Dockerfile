# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY atomic/report/ .

EXPOSE 5004

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "report.py"]