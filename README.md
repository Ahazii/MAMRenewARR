# MyAnonamouseRenewarr

A Docker-based web application for automating MyAnonamouse session management with qBittorrent and Prowlarr on Unraid servers.

## Features

- **Web Interface**: Basic and Advanced modes with config management
- **MAM Session Management**: Automated login and session cookie creation for qBittorrent/Prowlarr
- **IP Detection**: Fetches external IP and VPN container IP addresses
- **Session Cookie Creation**: Automated session creation with timestamp tracking
- **Old Session Cleanup**: Automated removal of expired MAM sessions
- **Automated Timer**: Scheduled task execution with configurable intervals and jitter
- **Timezone Support**: Proper timezone handling with automatic DST transitions
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

# Run container (with Docker socket and timezone support)
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
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

# Run container (with Docker socket and timezone support)
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped \
  mamrenewarr:latest
```

## Access

Visit `http://YOUR-UNRAID-IP:5000` in your browser.

## Usage

### Advanced Mode Workflow

1. **Step 1 - Get IPs**: Click to detect external and VPN IP addresses
2. **Step 2 - Login to MAM**: Automated browser login with session management
3. **Step 3 - qBittorrent Integration**: Connect to qBittorrent container and secure MAM session
4. **Step 4 - Prowlarr Integration**: Connect to Prowlarr container (planned)

#### Step 3 Details:
- **Log into qBittorrent**: Connect to `binhex-qbittorrentvpn` Docker container
- **Send Cookie to qBittorrent**: Execute curl command with MAM session cookie
- **Logout qBittorrent**: Clean disconnect from container

### Configuration

- **Basic Mode**: Simple one-click fixes and automated timer with configurable intervals
- **Advanced Mode**: Step-by-step session management workflow  
- **Config Page**: Set container names, paths, credentials, log levels, and timer settings
- **Settings Persistence**: Cookies, timestamps, and preferences saved automatically

#### Timer Configuration
- **Scheduled Run Time**: Set the time of day (HH:MM format) for automated tasks
- **Jitter**: Add random variance (±minutes) to prevent predictable scheduling
- **Run Interval**: Configure how many days between each run (1=daily, 7=weekly, etc.)
- **Timezone Support**: Container respects local timezone with automatic DST handling

## Development Status

- ✅ Web interface and Docker setup
- ✅ IP detection functionality  
- ✅ Configuration persistence
- ✅ MAM login automation with Selenium
- ✅ Session cookie creation for qBittorrent/Prowlarr
- ✅ Old session cleanup automation
- ✅ Cookie timestamp tracking
- ✅ Settings persistence (cookies, timestamps, log level)
- ✅ **Step 3: qBittorrent Docker integration with curl command execution**
- ✅ **Docker CLI integration with socket mounting**
- ✅ **Timer-based automation with configurable intervals and jitter**
- ✅ **Timezone support with automatic DST transitions**
- ✅ **MAM rate limit detection and user-friendly error messages**
- ✅ **Basic Mode: Complete workflow orchestration**
- ✅ **Advanced Mode: Step-by-step manual control**
- ✅ **Step 4: Prowlarr integration complete**
- ✅ **Duplicate logging fixed**

## Requirements

- Docker-enabled system (Unraid, Linux, Windows)
- **Docker socket access** (for container communication)
- Network access to qBittorrentVPN container (for log parsing)
- Port 5000 available
- `binhex-qbittorrentvpn` container running (for qBittorrent integration)
- Proper timezone configuration (use `-e TZ=Your/Timezone` in docker run)

## Author

Created by Ahazi

## License

MIT License
