# MyAnonamouseRenewarr

A Docker-based web application for automating MyAnonamouse session management with qBittorrent and Prowlarr on Unraid servers.

## Features

- **Web Interface**: Basic and Advanced modes with config management
- **MAM Session Management**: Automated login and session cookie creation for qBittorrent/Prowlarr
- **IP Detection**: Fetches external IP and VPN container IP addresses
- **Session Cookie Creation**: Automated session creation with timestamp tracking
- **Old Session Cleanup**: Automated removal of expired MAM sessions
- **Docker Ready**: Cross-platform container with production WSGI server
- **Theme Support**: Light/Dark mode toggle with persistence
- **Selenium Integration**: Browser automation for complex MAM interactions
- **Persistent Settings**: Configuration and session data saved automatically
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

## Usage

### Advanced Mode Workflow

1. **Step 1 - Get IPs**: Click to detect external and VPN IP addresses
2. **Step 2 - Login to MAM**: Automated browser login with session management
3. **Step 3 - Create Sessions**: Generate qBittorrent and Prowlarr session cookies
4. **Step 4 - Clean Old Sessions**: Remove expired sessions from MAM account

### Configuration

- **Basic Mode**: Simple one-click fixes and timer scheduling
- **Advanced Mode**: Step-by-step session management workflow  
- **Config Page**: Set container names, paths, credentials, and log levels
- **Settings Persistence**: Cookies, timestamps, and preferences saved automatically

## Development Status

- ✅ Web interface and Docker setup
- ✅ IP detection functionality  
- ✅ Configuration persistence
- ✅ MAM login automation with Selenium
- ✅ Session cookie creation for qBittorrent/Prowlarr
- ✅ Old session cleanup automation
- ✅ Cookie timestamp tracking
- ✅ Settings persistence (cookies, timestamps, log level)
- 🔄 Scheduled automation (timer-based execution)

## Requirements

- Docker-enabled system (Unraid, Linux, Windows)
- Network access to qBittorrentVPN container (for log parsing)
- Port 5000 available

## Author

Created by Ahazi

## License

MIT License
