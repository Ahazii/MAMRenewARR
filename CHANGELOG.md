# Changelog

## [Latest] - 2025-10-23

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
