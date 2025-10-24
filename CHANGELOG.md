# Changelog

## [Latest] - 2025-10-24

### Added
- **Progress Bars** - Modern horizontal progress bars for all operations in Basic and Advanced modes
- **Footer Status Tracking** - Persistent footer showing last MAM cookie push status (success/failure) with mode and timestamp
- **Mode Tracking** - Footer displays which mode performed the cookie push (Timer, Basic Mode - Fix All, Basic Mode - Fix MyAnonamouse, Advanced Mode)

### Fixed
- **400 Bad Request Error** - Fixed internal function calls by extracting send cookie logic from Flask route handler
- **Footer Status Updates** - Footer now correctly updates for both successful and failed operations
- **Missing Failure Tracking** - All error paths (curl failures, timeouts, exceptions) now save status to footer

### Changed
- Refactored qBittorrent send cookie function into internal function for direct calling without HTTP context
- Progress bars auto-hide after 5 seconds with color-coded status (blue=in-progress, green=success, red=failure)
- Footer status persists across container restarts

---

## [v1.x] - 2025-10-23

### Added
- **Run History Persistence** - History now survives container restarts
- **Timer Auto-Start** - Timer automatically resumes after container restart
- **Auto-Start Toggle** - Checkbox in Basic Mode to control auto-start behavior

### Fixed
- **Critical Startup Bug** - Fixed NameError preventing container from starting
- **Duplicate Logging** - Log entries no longer appear twice

### Changed
- Timer state now saved to settings.json
- History and auto-start loaded on app initialization

---

## [Previous Updates] - October 2025

### Added
- **Timer Interval Configuration** - Configurable days between runs (daily/weekly/monthly)
- **Timezone Support** - Proper timezone handling with automatic DST transitions
- **MAM Rate Limit Detection** - User-friendly error messages when rate limited
- **Current Server Time Display** - Live clock in Basic Mode
- **Jitter Configuration** - Random variance for timer scheduling

### Fixed
- Timer now correctly schedules next run after execution
- Container timezone matches host timezone
- Time calculations work correctly across DST transitions

---

## Core Features (Established)

- ✅ Web interface (Basic & Advanced modes)
- ✅ MAM login automation (Selenium)
- ✅ Session cookie creation for qBittorrent & Prowlarr
- ✅ Old session cleanup automation
- ✅ IP detection (external & VPN)
- ✅ Docker container integration
- ✅ qBittorrent integration via Docker socket
- ✅ Prowlarr integration via Selenium
- ✅ Settings persistence
- ✅ Theme support (light/dark)
- ✅ Configurable logging levels

---

**Repository**: https://github.com/Ahazii/MAMRenewARR
