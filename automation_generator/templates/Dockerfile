# Multi-stage build for Automation Generator
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install automation-generator package
COPY . /tmp/automation-generator
WORKDIR /tmp/automation-generator
RUN pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim as production

# Set labels
LABEL org.opencontainers.image.title="Automation Generator"
LABEL org.opencontainers.image.description="AI-powered automation script generator from SOPs"
LABEL org.opencontainers.image.source="https://github.com/automation-generator/automation-generator"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"

# Create application user
RUN groupadd --gid 1000 automation && \
    useradd --uid 1000 --gid automation --shell /bin/bash --create-home automation

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create directories
RUN mkdir -p /app/config /app/logs /app/data && \
    chown -R automation:automation /app

# Switch to non-root user
USER automation
WORKDIR /app

# Set default environment variables
ENV AUTOMATION_GENERATOR_HOST=0.0.0.0
ENV AUTOMATION_GENERATOR_PORT=8501
ENV AUTOMATION_GENERATOR_CONFIG_DIR=/app/config
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD automation-generator health || exit 1

# Expose port
EXPOSE 8501

# Default command
CMD ["automation-generator", "run", "--host", "0.0.0.0", "--port", "8501"]