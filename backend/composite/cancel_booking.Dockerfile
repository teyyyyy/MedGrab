FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the amqp_setup.py file directly to the same directory as cancel_booking.py
COPY rabbitmq/amqp_setup.py /app/composite/
COPY composite/cancel_booking.py /app/composite/
COPY config/.env /app/config/

# Expose the port the app runs on
EXPOSE 5005

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "composite/cancel_booking.py"]