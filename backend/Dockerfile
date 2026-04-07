FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY backend/ ./backend/

# Copy data sources (required by the agents)
COPY SourceData/    ./SourceData/
COPY SourceDataV1/  ./SourceDataV1/

WORKDIR /app/backend

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
