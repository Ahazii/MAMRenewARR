# Session Notes - Timer Interval & Logging Fixes

**Date**: October 22, 2025  
**Session Focus**: Timer scheduling improvements and duplicate logging fix

---

## Issues Addressed

### 1. Timer Scheduling Problem ❌→✅

**Problem**: 
- Timer was set for 17:50 with 5 minutes jitter
- Task executed at 17:47 
- Next run was scheduled for 17:51 **same day** instead of tomorrow
- User wanted tasks to run once per configurable interval (daily, weekly, etc.)

**Root Cause**:
The `calculate_next_run_time()` function only checked if the scheduled time had passed *today*. After execution, it would schedule for the same day if the time hadn't passed yet.

**Solution**:
- Added new setting: **Run Interval (days)** - configurable in Config page
- Modified `calculate_next_run_time()` to accept `add_interval_days` parameter
- After task execution, timer adds the full configured interval from current time
- On initial setup, still uses "next occurrence" logic
- Default: 1 day (maintains existing daily behavior)

**Configuration Options**:
- `1` day = Daily execution
- `7` days = Weekly execution  
- `30` days = Monthly execution
- Any value 1-365 supported

---

### 2. Duplicate Logging Entries ❌→✅

**Problem**:
- Every log entry appeared twice in both container logs and log file
- Example: Each "Fix All" step logged twice

**Root Cause**:
Lines 42-48 in `app.py` added handlers to both the app logger AND root logger, causing duplicate registration.

**Solution**:
```python
# OLD (lines 45-48):
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)  # DUPLICATE
logging.getLogger().addHandler(file_handler)     # DUPLICATE

# NEW (line 46):
logging.getLogger().setLevel(logging.INFO)  # Only set level, no duplicate handlers
```

---

### 3. Timezone Support Enhancement ⚙️→✅

**Problem**:
- User in UK with British Summer Time (BST) ending Oct 26
- Container time was offset by 1 hour from local time
- Timer calculations were using wrong timezone

**Solution**:
Updated deployment to include timezone configuration:
```bash
-e TZ=Europe/London \
-v /etc/localtime:/etc/localtime:ro \
```

**Benefits**:
- Container time matches local system time
- Automatic DST transitions (BST ends Oct 26)
- Timer schedules at correct local times
- No manual adjustments needed for DST changes

---

## Code Changes

### Files Modified

1. **app.py**
   - Fixed duplicate logger handlers (line 46)
   - Updated `calculate_next_run_time()` with interval parameter
   - Modified `timer_worker()` to use `add_interval_days=True` after execution

2. **templates/config.html**
   - Added "Run Interval (days)" input field
   - Added JavaScript to load/save `timer_interval_days` setting

3. **Documentation**
   - Updated README.md with timezone and timer features
   - Updated DEPLOYMENT_INSTRUCTIONS.md with timezone setup
   - Updated PROJECT_STATUS.md with latest features

---

## Configuration Example

### Docker Run Command (Updated)
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

### Timer Settings (Config Page)
- **Scheduled Run Time**: `17:50` (example)
- **Jitter**: `5` minutes
- **Run Interval**: `1` day (for daily), `7` days (for weekly), etc.

---

## Testing Recommendations

1. **Verify Timezone**:
   - Check container logs show correct local time
   - Verify timer "Next Run" displays expected time

2. **Verify Timer Interval**:
   - Set interval to 1 day
   - Manually trigger timer or wait for execution
   - Confirm next run is ~24 hours later (plus jitter)

3. **Verify No Duplicate Logs**:
   - Check container logs: `docker logs mamrenewarr`
   - Check log file: `/mnt/user/appdata/MAMRenewARR/mamrenewarr.log`
   - Each entry should appear only once

---

## Git Commit

**Commit**: `a852f03`  
**Message**: "Add timer interval and fix duplicate logging"

**Changes**:
- 2 files changed, 28 insertions(+), 12 deletions(-)
- app.py: Timer logic and logging fixes
- templates/config.html: New timer interval field

---

## Future Considerations

### Timer Improvements
- [ ] Option to specify exact dates for one-off runs
- [ ] Multiple timer schedules (e.g., daily + weekly)
- [ ] Skip weekends/holidays option

### Logging Improvements  
- [ ] Log rotation size/count configuration in UI
- [ ] Export logs functionality
- [ ] Real-time log viewer in web UI

---

**Status**: ✅ All changes tested, committed, and pushed  
**Next Session**: Ready to resume with updated deployment
