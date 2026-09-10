# ==============================================================================
# Multi-Stage Dockerfile for SWAYAMBHU v2 (Frontend + Backend Unified Container)
# ==============================================================================

# ----------------- Stage 1: Build the React/Vite Frontend -----------------
FROM node:20-slim AS frontend-builder
WORKDIR /app/premanand-ji-website

# Install frontend dependencies
COPY premanand-ji-website/package*.json ./
RUN npm install

# Copy frontend source and build static assets
COPY premanand-ji-website/ ./
RUN npm run build

# ----------------- Stage 2: Production Python API Backend -----------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install build tools needed for native python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-install CPU-only PyTorch so pip doesn't download 2.5GB of NVIDIA CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server and RAG pipeline code
COPY config.py schema.py indexer.py rag_engine.py server.py ./
COPY data/ ./data/

# Copy built frontend from Stage 1 so server.py mounts it automatically at /
COPY --from=frontend-builder /app/premanand-ji-website/dist/public ./premanand-ji-website/dist/public

EXPOSE 8080

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
