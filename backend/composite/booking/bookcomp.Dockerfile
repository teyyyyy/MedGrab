FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY composite/booking/booking.py ./booking.py
COPY composite/booking/amqp_lib.py ./amqp_lib.py
COPY composite/booking/amqp_setup.py ./amqp_setup.py

EXPOSE 5008

CMD ["python", "booking.py"]
