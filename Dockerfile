FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Configure environment
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from openenv_customer_support import CustomerSupportTriageEnv; CustomerSupportTriageEnv('easy').reset('easy')"

# For HF Spaces: run the FastAPI + Gradio hybrid app
CMD ["python", "spaces_app.py"]
