# Nepal Industrial Decarbonization Platform - root Dockerfile
#
# This is the official single-image build for the platform.
# It builds the `pro` package (the Python application) and runs the
# FastAPI server on port 8000.
#
# The pro/Dockerfile remains as the multi-stage build for the
# Streamlit dashboard on port 8501.
#
# Build:
#   docker build -t nepal-decarb:dev .
#
# Run:
#   docker run -p 8000:8000 nepal-decarb:dev
#
# Healthcheck:
#   curl http://localhost:8000/api/status

FROM python:3.11-slim

WORKDIR /app

# System dependencies. libgomp1 is required by numba; weasyprint needs
# libpango and libffi; reportlab needs libfreetype. The full list of
# native libs is documented in pro/Dockerfile.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libgomp1 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libffi-dev \
        libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching for code-only changes)
COPY pro/pyproject.toml pro/README.md ./pro/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "./pro[nepal_decarb_pro]" 2>/dev/null || \
    pip install --no-cache-dir -e "./pro"

# Copy the rest of the source
COPY pro/ ./pro/
COPY tools/ ./tools/
COPY docs/ ./docs/

# Re-install in editable mode so the source is live
RUN pip install --no-cache-dir -e "./pro"

# Default port
EXPOSE 8000

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/api/status || exit 1

# Run the FastAPI server (the pro/nepal_decarb_pro/api.py entry point)
CMD ["uvicorn", "nepal_decarb_pro.api:app", "--host", "0.0.0.0", "--port", "8000"]
