# Dockerfile for MyAnonamouseRenewarr
# Cross-platform: Windows Docker Desktop (test) and Unraid/Linux (target)

FROM python:3.12-slim

# Set environment variables for cross-platform compatibility
ENV PYTHONUNBUFFERED=1 \
    TZ=UTC

# Install system dependencies for Chrome, ChromeDriver, and Docker CLI
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    apt-transport-https \
    lsb-release \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver - use webdriver-manager approach
RUN pip install webdriver-manager

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Expose port for Flask app (use 5000 by default)
EXPOSE 5000

# Use Waitress for production-ready serving (cross-platform)
CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app:app"]
