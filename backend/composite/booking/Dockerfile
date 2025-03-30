FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY booking.py .

EXPOSE 5008

CMD ["python", "booking.py"]
