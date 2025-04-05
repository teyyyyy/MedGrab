FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY composite/ .

EXPOSE 5008

ENV PYTHONUNBUFFERED=1

CMD ["python", "booking.py"]
