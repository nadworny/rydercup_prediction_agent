# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY ryder_cup_prediction/ ./ryder_cup_prediction/
COPY mcp_servers/ ./mcp_servers/
COPY .env.example .env

# Expose port for adk server
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default to web UI, but can be overridden
ENV ADK_MODE=web

# Run adk server (web or api_server based on ADK_MODE)
CMD if [ "$ADK_MODE" = "api" ]; then \
      uv run adk api_server --host 0.0.0.0 --port 8000; \
    else \
      uv run adk web --host 0.0.0.0 --port 8000; \
    fi
