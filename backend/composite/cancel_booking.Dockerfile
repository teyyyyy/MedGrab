FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY composite/amqp_setup.py /app/composite/
COPY composite/cancel_booking.py /app/composite/
COPY .env /app/

# Expose the port the app runs on
EXPOSE 5005

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "composite/cancel_booking.py"]