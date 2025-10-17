# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

MAMRenewARR is a Docker-based Flask web application for automating MyAnonamouse session management with qBittorrent and Prowlarr integration on Unraid servers. The application provides both Basic and Advanced modes for managing VPN and torrent client configurations.

## Common Development Commands

### Docker Operations
```bash
# Build the Docker image
docker build -t mamrenewarr:latest .

# Run for development (with hot reload)
python app.py

# Run production container with qBittorrent log access
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped \
  mamrenewarr:latest

# Stop and remove existing container
docker stop mamrenewarr && docker rm mamrenewarr

# View container logs
docker logs mamrenewarr
```

### Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Flask app locally (development mode)
python app.py

# Access the web interface
# Local: http://localhost:5000
# Unraid: http://YOUR-UNRAID-IP:5000
```

### Deployment
```bash
# Full rebuild and deploy cycle (Unraid)
cd /mnt/user/appdata/MAMRenewARR
git pull origin main
docker stop mamrenewarr && docker rm mamrenewarr
docker build -t mamrenewarr:latest .
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped \
  mamrenewarr:latest
```

## Architecture Overview

### Core Structure
- **Flask Application**: Single-file Flask app (`app.py`) serving web interface and REST API
- **Templates**: Jinja2 HTML templates in `/templates/` with shared base template
- **Configuration**: JSON-based settings persistence in `/app/data/settings.json`
- **Docker**: Production deployment using Waitress WSGI server

### Key Components

#### Flask Routes
- `/` - Redirects to Basic mode
- `/basic` - Simple one-click fixes and timer scheduling interface
- `/advanced` - Step-by-step session management workflow
- `/config` - Configuration management interface
- `/api/settings` - GET/POST endpoints for settings persistence
- `/api/get_ips` - IP detection service (external and VPN IPs)

#### IP Detection System
The application implements multiple fallback methods for VPN IP detection:
1. **Log File Method**: Parses qBittorrentVPN container logs for `Detected external IP` entries
2. **API Fallback**: Uses `ipinfo.io` as secondary detection method
3. **External IP**: Always fetches via `api.ipify.org`

#### Configuration Management
- Settings stored in `/app/data/settings.json` (mounted from Unraid appdata)
- Default qBittorrentVPN log path: `/app/binhex-qbittorrentvpn/qBittorrent/data/logs/qbittorrent.log`
- Supports custom container names and log paths

### Template Hierarchy
- `base.html`: Shared layout with navigation, theme toggle, and styling
- `basic.html`: Simple interface for basic operations
- `advanced.html`: Multi-step workflow interface with IP detection
- `config.html`: Settings management form
- Built-in light/dark theme support with localStorage persistence

## File Organization

```
/
├── app.py                 # Main Flask application
├── Dockerfile            # Multi-stage container build
├── requirements.txt      # Python dependencies (Flask, Waitress, requests)
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Shared layout and styling
│   ├── basic.html       # Basic mode interface
│   ├── advanced.html    # Advanced mode interface
│   └── config.html      # Configuration interface
├── README.md            # User documentation
├── PROJECT_SUMMARY.md   # Development status and notes
└── DEPLOYMENT_INSTRUCTIONS.md  # Updated deployment guide
```

## Development Context

### Current Implementation Status
- ✅ Web interface with Basic/Advanced modes
- ✅ IP detection (external and VPN)
- ✅ Configuration persistence
- ✅ Docker containerization with Waitress
- ✅ Theme support (light/dark modes)
- 🔄 MAM automation features (planned)
- 🔄 qBittorrent/Prowlarr integration (planned)

### Key Technical Details
- **Target Environment**: Primarily designed for Unraid Docker deployment
- **Production Server**: Uses Waitress WSGI server (cross-platform compatible)
- **Volume Mounting**: Configuration persists via `/app/data` volume mount
- **Log Access**: Requires read-only mount of qBittorrentVPN logs for VPN IP detection
- **Port**: Application runs on port 5000 by default

### Important Deployment Notes
- Configuration file location changed from `/app/settings.json` to `/app/data/settings.json`
- VPN IP detection requires proper log file mounting or falls back to API detection
- Container no longer requires Docker CLI access (resolved "docker command not found" errors)
- Settings persistence verified through Unraid appdata folder integration

## Integration Points

### qBittorrentVPN Integration
- Reads log files to extract VPN IP addresses
- Requires read-only mount: `-v /path/to/qbittorrent/logs:/app/binhex-qbittorrentvpn/qBittorrent/data/logs:ro`
- Parses log entries with regex: `Detected external IP. IP: "?([0-9]{1,3}(?:\.[0-9]{1,3}){3})"?`

### Unraid Specific Configuration
- Appdata persistence: `/mnt/user/appdata/MAMRenewARR`
- Container restart policy: `unless-stopped`
- Network mode: Bridge (port 5000 exposed)