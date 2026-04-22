# Smart City Navigator Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Backend
FROM python:3.11-slim as backend

WORKDIR /app/backend

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create models and data directories
RUN mkdir -p models data

# Stage 2: Frontend
FROM node:20-alpine as frontend

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 3: Production
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from stage 1
COPY --from=backend /app/backend /app/backend

# Copy built frontend from stage 2
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
