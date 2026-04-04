FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY stop_monitoring.py .

CMD ["python", "stop_monitoring.py"]