# Deployment Guide

## Requirements

- Docker with socket access: `/var/run/docker.sock` (for container communication)
- `binhex-qbittorrentvpn` container running
- Port 5000 available (or custom via `PORT` env var)

---

## Unraid Template (Recommended)

### Method 1: Community Applications (Coming Soon)
1. Go to **Apps** tab in Unraid
2. Search for `MAMRenewARR`
3. Click **Install**

### Method 2: Manual Template
1. Go to **Docker** tab → **Add Container**
2. Under **Template repositories**, add:
   ```
   https://raw.githubusercontent.com/Ahazii/MAMRenewARR/main/mamrenewarr.xml
   ```
3. Select **MAMRenewARR** from template dropdown
4. Configure settings:
   - **WebUI Port**: 5000 (or custom)
   - **Data Path**: `/mnt/user/appdata/MAMRenewARR`
   - **Timezone**: Your timezone (e.g. `Europe/London`)
5. Click **Apply**

**Access**: `http://YOUR-UNRAID-IP:5000`

---

## Manual Docker Installation

### Using GitHub Container Registry (GHCR)

```bash
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  -v /etc/localtime:/etc/localtime:ro \
  --restart unless-stopped \
  ghcr.io/ahazii/mamrenewarr:main
```

### Building from Source

```bash
cd /mnt/user/appdata
git clone https://github.com/Ahazii/MAMRenewARR
cd MAMRenewARR
docker build -t mamrenewarr:latest .
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  -v /etc/localtime:/etc/localtime:ro \
  --restart unless-stopped \
  mamrenewarr:latest
```

---

## Updates

### Unraid Template
1. Go to **Docker** tab
2. Click **Check for Updates**
3. Click **Update** if available

### Manual (GHCR)
```bash
docker pull ghcr.io/ahazii/mamrenewarr:main
docker stop mamrenewarr && docker rm mamrenewarr
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  -v /etc/localtime:/etc/localtime:ro \
  --restart unless-stopped \
  ghcr.io/ahazii/mamrenewarr:main
```

### From Source
```bash
cd /mnt/user/appdata/MAMRenewARR
git pull origin main
docker build -t mamrenewarr:latest .
docker stop mamrenewarr && docker rm mamrenewarr
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  -v /etc/localtime:/etc/localtime:ro \
  --restart unless-stopped \
  mamrenewarr:latest
```

---

## Timezone Configuration

Replace `Europe/London` in the docker run command with your timezone:

| Region | Timezone | DST Handling |
|--------|----------|-------------|
| **UK** | `Europe/London` | ✅ Auto (BST) |
| **France** | `Europe/Paris` | ✅ Auto (CEST) |
| **Germany** | `Europe/Berlin` | ✅ Auto (CEST) |
| **Spain** | `Europe/Madrid` | ✅ Auto (CEST) |
| **Italy** | `Europe/Rome` | ✅ Auto (CEST) |
| **Netherlands** | `Europe/Amsterdam` | ✅ Auto (CEST) |
| **Belgium** | `Europe/Brussels` | ✅ Auto (CEST) |
| **Poland** | `Europe/Warsaw` | ✅ Auto (CEST) |
| **Sweden** | `Europe/Stockholm` | ✅ Auto (CEST) |
| **Norway** | `Europe/Oslo` | ✅ Auto (CEST) |
| US East | `America/New_York` | ✅ Auto |
| US West | `America/Los_Angeles` | ✅ Auto |
| Asia | `Asia/Tokyo` | No DST |

**Note**: All timezones automatically handle Daylight Saving Time (DST) transitions.

---

## Volume Mounts Explained

The docker run command includes several volume mounts:

| Mount | Purpose |
|-------|--------|
| `/var/run/docker.sock` | **Docker Socket** - Allows container to restart qBittorrent/Prowlarr containers |
| `/etc/localtime` | **System Time** - Syncs container time with host timezone |
| `/app/data` | **Persistent Storage** - Saves settings, cookies, and run history |
| `/app/shared/qbittorrent-logs` | **VPN IP Detection** - Reads qBittorrent logs to detect VPN IP |

**Important**: The Docker socket mount (`/var/run/docker.sock`) is required for the container restart functionality in Advanced Mode.

---

## Troubleshooting

**Container won't start:**
```bash
docker logs mamrenewarr
```

**Check if running:**
```bash
docker ps | grep mamrenewarr
```

**Restart container:**
```bash
docker restart mamrenewarr
```

**View settings:**
```bash
cat /mnt/user/appdata/MAMRenewARR/settings.json
```

**View logs:**
```bash
cat /mnt/user/appdata/MAMRenewARR/mamrenewarr.log
```
Or use the web interface: `http://YOUR-IP:5000/logs`

---

## Port Configuration

To use a custom port (e.g., 8080 instead of 5000):

```bash
-p 8080:8080 -e PORT=8080
```

**Unraid**: Change "WebUI Port" and "Application Port" in template settings.

---

## GitHub Actions Auto-Build

The repository includes a GitHub Actions workflow that automatically builds and pushes images to GHCR on every push to `main`.

**Important**: Ensure the GHCR package is set to **Public**:
1. Go to: https://github.com/users/Ahazii/packages/container/mamrenewarr/settings
2. Scroll to "Danger Zone" → "Change visibility"
3. Set to **Public**
