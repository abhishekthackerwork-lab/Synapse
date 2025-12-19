# -------------------------------
# 1. Base Image: Lightweight Python 3.12
# -------------------------------
FROM python:3.12-slim

# 2. Env settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Work directory
WORKDIR /app

# -------------------------------
# 4. Install system dependencies
# -------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# 5. Install Python dependencies
# -------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# 6. Copy source code (including local model)
# -------------------------------
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY .env ./
# If you do NOT have these files, ignore them.

# Model folder is inside app/models, already included above.

# -------------------------------
# 7. Default command
# -------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
