# Dockerfile for MyAnonamouseRenewarr
# Cross-platform: Windows Docker Desktop (test) and Unraid/Linux (target)

FROM python:3.12-slim

# Set environment variables for cross-platform compatibility
ENV PYTHONUNBUFFERED=1 \
    TZ=UTC

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Flask app (use 5000 by default)
EXPOSE 5000

# Use Waitress for production-ready serving (cross-platform)
CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app:app"]
