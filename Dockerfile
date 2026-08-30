# ==============================================================
# RPM System — Production Dockerfile (used by Railway)
# ==============================================================
FROM python:3.11-slim

# libgomp1 is required at runtime for scikit-learn's compiled kernels
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/usr/local -r requirements.txt

# Copy the application (see .dockerignore — excludes .env and secrets)
COPY app ./app
COPY database ./database
COPY .streamlit ./.streamlit

EXPOSE 8501

# Railway injects $PORT (e.g. 80). Streamlit needs to bind to it.
# Note: `python -m streamlit` (not bare `streamlit`) so that "/app" is on
# sys.path and `from app.core...` imports resolve inside the container.
CMD ["/bin/sh", "-c", "python -m streamlit run app/main.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true"]