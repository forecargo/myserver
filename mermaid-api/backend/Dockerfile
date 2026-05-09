# Stage 1: React ビルド
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI + 静的ファイル配信
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-builder /frontend/dist ./static
RUN mkdir -p /app/data
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
