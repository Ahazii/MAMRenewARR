# Deployment Guide

## Requirements

- Docker socket access: `/var/run/docker.sock` (for container communication)
- `binhex-qbittorrentvpn` container running
- Port 5000 available

---

## Initial Setup

```bash
cd /mnt/user/appdata
git clone https://github.com/Ahazii/MAMRenewARR
cd MAMRenewARR
docker build -t mamrenewarr:latest .
docker run -d --name mamrenewarr -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped mamrenewarr:latest
```

---

## Updates

```bash
cd /mnt/user/appdata/MAMRenewARR
git pull origin main
docker build -t mamrenewarr:latest .
docker stop mamrenewarr && docker rm mamrenewarr
docker run -d --name mamrenewarr -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped mamrenewarr:latest
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
