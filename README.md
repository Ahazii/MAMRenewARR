# MyAnonamouseRenewarr

A Docker-based web application for automating MyAnonamouse session management with qBittorrent and Prowlarr on Unraid servers.

## Features

- **Web Interface**: Basic and Advanced modes with config management
- **IP Detection**: Fetches external IP and VPN container IP addresses
- **Docker Ready**: Cross-platform container with production WSGI server
- **Theme Support**: Light/Dark mode toggle with persistence
- **Unraid Optimized**: Designed for Unraid Docker deployment

## Quick Start (Unraid)

### Option 1: Pull Pre-built Image (Recommended)

```bash
# Pull the latest image
docker pull ghcr.io/yourusername/mamrenewarr:latest

# Create persistent storage
mkdir -p /mnt/user/appdata/MAMRenewARR

# Run container
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  --restart unless-stopped \
  ghcr.io/yourusername/mamrenewarr:latest
```

### Option 2: Build from Source

```bash
# Clone repository
git clone https://github.com/yourusername/mamrenewarr.git
cd mamrenewarr

# Build image
docker build -t mamrenewarr:latest .

# Run container
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  --restart unless-stopped \
  mamrenewarr:latest
```

## Access

Visit `http://YOUR-UNRAID-IP:5000` in your browser.

## Configuration

- **Basic Mode**: Simple one-click fixes and timer scheduling
- **Advanced Mode**: Step-by-step session management workflow
- **Config Page**: Set container names, paths, and credentials

## Development Status

- ✅ Web interface and Docker setup
- ✅ IP detection functionality
- ✅ Configuration persistence
- 🔄 MAM automation features (in development)
- 🔄 qBittorrent/Prowlarr integration (in development)

## Requirements

- Docker-enabled system (Unraid, Linux, Windows)
- Network access to qBittorrentVPN container (for log parsing)
- Port 5000 available

## Author

Created by Ahazi

## License

MIT License
