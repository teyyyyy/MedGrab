FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY atomic/stripeatomic/ .

EXPOSE 5010

ENV PYTHONUNBUFFERED=1

CMD ["python", "stripeatomic.py"]