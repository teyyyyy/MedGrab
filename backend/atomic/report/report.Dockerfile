FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY atomic/report/ .

EXPOSE 5004

ENV PYTHONUNBUFFERED=1

CMD ["python", "report.py"]