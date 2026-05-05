# ================================
# 📦 Base image
# ================================
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    unzip \
    git \
    libpq-dev \
    gcc \
    tar \
    python3 \
    libstdc++6 \
    libncurses6 \
    libncurses-dev \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# 5️⃣ Python deps
COPY --chown=appuser:appuser backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt
COPY --chown=appuser:appuser backend/ ./backend/

USER appuser

# ================================
# 🚀 RUN BACKEND
# ================================
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
