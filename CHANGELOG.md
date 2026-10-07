# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Night mode** (`nothing-night`, hyprsunset): smooth fade, warmth presets, schedule with
  presets or custom times; manual toggles override until the next scheduled switch.
  In the settings hub, as a control-center tile, `Super+Ctrl+N`, and a moon in the island.
- **Boot lock** (`./install.sh --boot-lock`): greetd autologin starts Hyprland already
  locked by hyprlock, replacing the KDE-styled login screen; `--restore-login` undoes it.

### Changed
- Idle: lock after 15 minutes (was 5), screens off at 15:30, suspend after 1 hour (was 30 minutes).

## [1.0.0] — 2026-10-07

### Added
- `nothing-shell`: GTK3 layer-shell daemon with a hover-to-expand **dynamic island**
  (workspaces, weather, clock, calendar, MPRIS media, volume, network/Bluetooth) and a
  **control center** (dot-matrix CPU graph, RAM, thermals, toggles, notification history,
  power actions with two-step confirm).
- Rofi **power overlay** with single-key accelerators (`p r s l e`, `Esc`).
- Rofi **settings hub** (`Super+I`, also a *Settings* launcher entry) and keybinding cheat-sheet.
- Nothing-styled **hyprlock** (dot-matrix clock, battery/AC, now playing, layout chip).
- **hypridle** chain: warn → lock → screens off → suspend.
- kitty monochrome theme, launcher theme, Waybar logo + status pill, desktop widgets.
- Idempotent `install.sh` (packages, keyboard, services, fonts, backup + symlinks, verify).
- `make check` / CI: shellcheck, ruff, JSON(C) validation, `Hyprland --verify-config`.

### Fixed
- Keyboard layout is Austrian German without dead keys (`at` / `nodeadkeys`) in Hyprland,
  hyprlock, login screen and TTY (was hard-coded `us`).
- One lock screen only — every lock path goes through `loginctl lock-session` → hypridle → hyprlock.
- Hyprland 0.56 dispatch syntax (`hl.dsp.*`) everywhere; the old `hyprctl dispatch exit` /
  `dpms on` forms fail silently on 0.56.
- `bluetoothctl` no longer hangs the widgets when `bluetooth.service` is stopped.
- Live-music equaliser in the island is vertically centred.

[Unreleased]: https://github.com/doveyQ/dotfiles/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/doveyQ/dotfiles/releases/tag/v1.0.0
