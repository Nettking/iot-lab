FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app \
    IOT_LAB_CONFIG=/app/config/config.yaml

CMD ["python", "-m", "gateway.main"]
