# Deployment Guide

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

Replace `Europe/London` with your timezone:

| Region | Timezone |
|--------|----------|
| UK | `Europe/London` |
| US East | `America/New_York` |
| US West | `America/Los_Angeles` |
| Europe | `Europe/Paris` or `Europe/Berlin` |
| Asia | `Asia/Tokyo` or `Asia/Singapore` |

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
