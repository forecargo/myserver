FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=600 -r requirements.txt
COPY . .
CMD ["uvicorn", "viewer:app", "--host", "0.0.0.0", "--port", "8005"]
