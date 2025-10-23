# Session State - October 23, 2025

## Session Summary

Successfully enhanced MAMRenewARR container with Unraid template support, configurable port, and web-based log viewer.

---

## Changes Implemented

### 1. Unraid Template (`mamrenewarr.xml`)
**Status**: ✅ Complete and deployed

**Created**: Official Unraid Community Applications template
- **Repository**: `ghcr.io/ahazii/mamrenewarr:main`
- **WebUI**: `http://[IP]:[PORT:5000]`
- **Icon**: `https://raw.githubusercontent.com/Ahazii/MAMRenewARR/main/icon.png`

**Configuration Options**:
- WebUI Port (default: 5000)
- Data path (`/app/data`)
- Docker socket (`/var/run/docker.sock`)
- qBittorrent logs path (optional)
- Timezone (default: Europe/London)
- Application PORT variable (advanced)

**Fixes**:
- ✅ Resolves "3rd Party" version display issue
- ✅ Enables working WebUI icon in Unraid Docker tab
- ✅ Proper category placement (Downloaders)
- ✅ Support and project links

---

### 2. Configurable Port Support
**Status**: ✅ Complete

**Files Modified**:
- `Dockerfile`: Added `PORT` environment variable (default: 5000)
- `app.py`: Updated to read `PORT` from environment

**Usage**:
```bash
-p 8080:8080 -e PORT=8080
```

**Benefits**:
- Allows users to run on custom ports
- Prevents port conflicts with existing services
- Configurable via Unraid template (advanced settings)

---

### 3. Web-Based Log Viewer
**Status**: ✅ Complete

**Files Created**:
- `templates/logs.html`: Full-featured log viewer interface

**Files Modified**:
- `app.py`: Added `/logs` route and `/api/logs` API endpoint
- `templates/base.html`: Added "Logs" to navigation menu

**Features**:
- Real-time log viewing in browser
- Auto-refresh every 5 seconds (toggleable)
- Adjustable line count (100, 200, 500, 1000, or all)
- Auto-scroll to bottom
- Dark theme matching existing UI
- Shows line count statistics

**API Endpoint**:
```
GET /api/logs?lines=200
Response: { success: true, logs: "...", total_lines: 1234 }
```

---

### 4. Icon Asset
**Status**: ✅ Complete

**Created**: `icon.png`
- 512x512 PNG image
- Blue background (#1e3a8a)
- White "MAM" text
- Used by Unraid template

---

### 5. GitHub Container Registry (GHCR)
**Status**: ✅ Deployed and Public

**Actions Taken**:
1. GitHub Actions workflow builds on every push to `main`
2. Package visibility set to **Public** (was private initially)
3. Image available at: `ghcr.io/ahazii/mamrenewarr:main`

**Workflow**: `.github/workflows/docker-build.yml`
- Auto-builds on push/PR to main
- Tags: `main`, `latest`, semver tags
- Uses GitHub token for authentication

---

### 6. Documentation Updates
**Status**: ✅ Complete

**Files Updated**:
- `README.md`: 
  - Added Unraid template installation instructions
  - Added log viewer feature documentation
  - Updated port configuration section
  - Updated quick start with GHCR image
  
- `DEPLOYMENT.md`:
  - Added Unraid template deployment methods
  - Updated manual installation with GHCR
  - Added port configuration section
  - Added GitHub Actions auto-build documentation
  - Added log viewing instructions

---

## Git Commits

1. **Commit 7b98008**: "Add Unraid template, configurable port, and log viewer"
   - Created `mamrenewarr.xml`
   - Updated `Dockerfile` with PORT env var
   - Updated `app.py` with port config and log routes
   - Created `templates/logs.html`
   - Updated navigation in `base.html`
   - Generated `icon.png`

2. **Commit 0ea1211**: "Fix template tag to use :main"
   - Changed template to use `:main` tag instead of `:latest`

3. **Current Session**: Documentation updates (pending commit)

---

## Configuration Details

### Environment Variables
- `PORT`: Application port (default: 5000)
- `TZ`: Timezone (default: UTC)
- `PYTHONUNBUFFERED`: Set to 1 for logging

### Volume Mounts
- `/app/data`: Persistent storage (settings, logs, history)
- `/var/run/docker.sock`: Docker socket for container management
- `/app/shared/qbittorrent-logs`: qBittorrent logs (read-only)
- `/etc/localtime`: System timezone sync (read-only)

### Port Mapping
- Container listens on `${PORT}` (default: 5000)
- Map with `-p HOST_PORT:CONTAINER_PORT`
- Example: `-p 8080:8080 -e PORT=8080`

---

## Log Management

### Log File Configuration (Already Implemented)
- **File**: `/app/data/mamrenewarr.log`
- **Handler**: `RotatingFileHandler`
- **Max Size**: 10MB per file
- **Backup Count**: 5 files
- **Total Size**: 50MB maximum
- **Levels**: INFO (default), DEBUG (configurable in UI)

### Log Viewer Features
- Access: `http://YOUR-IP:5000/logs`
- Auto-refresh: 5 seconds (toggleable)
- Line counts: 100, 200, 500, 1000, all
- Real-time updates while container runs

---

## Deployment Options

### Option 1: Unraid Template (Recommended)
```
Docker Tab → Add Container → Template URL:
https://raw.githubusercontent.com/Ahazii/MAMRenewARR/main/mamrenewarr.xml
```

### Option 2: Docker Command (GHCR)
```bash
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --restart unless-stopped \
  ghcr.io/ahazii/mamrenewarr:main
```

### Option 3: Build from Source
```bash
cd /mnt/user/appdata
git clone https://github.com/Ahazii/MAMRenewARR
cd MAMRenewARR
docker build -t mamrenewarr:latest .
docker run -d --name mamrenewarr -p 5000:5000 ...
```

---

## Issues Resolved

### Issue 1: "3rd Party" Version Display
**Problem**: Container showed as "3rd Party" in Unraid Docker version column
**Cause**: No Unraid template with proper metadata
**Solution**: Created `mamrenewarr.xml` with Repository, Icon, and WebUI tags

### Issue 2: Non-Working WebUI Icon
**Problem**: WebUI icon in Unraid Docker tab didn't work
**Cause**: No template with WebUI configuration
**Solution**: Added `<WebUI>` and `<Icon>` tags to template

### Issue 3: Hardcoded Port
**Problem**: Application only ran on port 5000
**Cause**: Port hardcoded in Dockerfile CMD and app.py
**Solution**: Added `PORT` environment variable with default value

### Issue 4: GHCR Access Denied
**Problem**: `docker pull ghcr.io/ahazii/mamrenewarr:main` returned "denied"
**Cause**: GitHub Container Registry package was set to private by default
**Solution**: Changed package visibility to Public in GitHub settings

### Issue 5: No Web-Based Log Access
**Problem**: Users had to SSH/console to view logs
**Cause**: No log viewer in web interface
**Solution**: Created `/logs` page with real-time viewer and API endpoint

---

## Testing Checklist

✅ Unraid template pulls image successfully
✅ WebUI icon displays in Unraid Docker tab
✅ WebUI link works from Docker tab
✅ Port configuration via environment variable
✅ Log viewer accessible at `/logs`
✅ Log viewer auto-refresh works
✅ Log viewer line count selector works
✅ GitHub Actions builds image on push
✅ GHCR package is public
✅ Documentation updated (README, DEPLOYMENT)

---

## Next Steps (Optional Future Enhancements)

1. **Community Applications Submission**
   - Submit template to Unraid Community Applications repo
   - Requires fork of: https://github.com/Squidly271/docker-templates

2. **Version Tagging**
   - Consider semantic versioning (v1.0.0)
   - GitHub Actions workflow supports semver tags

3. **Log Viewer Enhancements**
   - Add log filtering (search/regex)
   - Add log level filtering
   - Add download log file button
   - Add clear logs button

4. **Better Icon**
   - Replace placeholder with custom designed icon
   - Use MyAnonamouse branding elements

5. **Update Notifications**
   - Check GitHub releases for updates
   - Display notification in UI when update available

---

## Files Changed This Session

### Created
- `mamrenewarr.xml` - Unraid template
- `icon.png` - Container icon
- `templates/logs.html` - Log viewer page
- `SESSION_STATE_2025-10-23.md` - This file

### Modified
- `Dockerfile` - Added PORT env var
- `app.py` - Added PORT config and log routes
- `templates/base.html` - Added Logs navigation link
- `README.md` - Updated documentation
- `DEPLOYMENT.md` - Updated deployment instructions

---

## Repository State

- **Branch**: main
- **Latest Commit**: 0ea1211 "Fix template tag to use :main"
- **Docker Image**: `ghcr.io/ahazii/mamrenewarr:main` (public)
- **Template URL**: `https://raw.githubusercontent.com/Ahazii/MAMRenewARR/main/mamrenewarr.xml`
- **Documentation**: ✅ Updated and complete

---

## Conclusion

All requested enhancements have been successfully implemented, tested, and deployed:
- ✅ Log handling (already excellent, added web viewer)
- ✅ Unraid template fixes (version and WebUI icon)
- ✅ Configurable port support

The container is now fully production-ready with proper Unraid integration and user-friendly features.
