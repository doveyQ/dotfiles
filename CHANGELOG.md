# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed — Copenhagen redesign
- **New look**: warm-neutral Nordic palette (chalk · stone · smoke · sage · clay · sand ·
  slate), smoky frosted glass, no red, no pure white. Windows get 1px low-contrast outlines
  (or none: `borderless = true`), 14px continuous-curve corners and deep soft shadows; the red
  focus glow is gone (optional sage *Soft glow* in Settings).
- **Typography**: SF Pro Text / Display and SF Mono replace the Ndot dot-matrix fonts;
  `fontconfig/` maps them to Inter / Inter Display / JetBrains Mono when Apple's fonts aren't
  installed. The installer no longer downloads the Nothing fonts.
- **One continuous top bar** instead of separate pills: launcher · island (now the bar's
  transparent centre) · hover drawer (tray, CPU, memory) · network speed · Wi-Fi · clipboard ·
  battery · notifications · quick settings · power.
- **Themes**: every colour and font lives in `hypr/themes/<name>/` (`theme.lua`,
  `palette.css`, `palette.rasi`, `hyprlock.conf`, `kitty.conf`, `fonts.conf`); the symlink
  `hypr/theme` selects the active one. nothing-shell reads its drawing colours from the palette.
- **Modular Hyprland config**: `hyprland.lua` is now a loader for `hypr/conf/`
  (`monitors`, `autostart`, `input`, `look`, `rules`, `keybinds`).
- Restyled to match: island + control center, Settings app, SwayNC, rofi launcher / session
  menu, dock, kitty, hyprlock, desktop widgets. Title-case labels instead of all-caps.
- New default wallpaper `hypr/wallpapers/copenhagen.jpg`.

### Added
- **Settings app** (`Super+I`, launcher entry *Settings*): Network, Bluetooth, Sound, Displays,
  Appearance, Night mode, Notifications, Keyboard & mouse, Power & lock, Login screen,
  Shortcuts, About — all live, with *Install* buttons for missing helpers and a 15 s
  keep/revert prompt for display changes. Replaces the Rofi settings hub.
- **`nothing-settings` CLI** with the same backend: `list`, `get`, `set`, `reset`, `wifi …`, `bt …`.
- Settings are stored per machine in `~/.config/nothing/` (generated `settings.lua`,
  `hypridle.conf`, `hyprpaper.conf`) — outside the repo; they win over the machine file.
- `make selftest`: opens every Settings page and fires every control with a stubbed backend.

### Changed
- The installer now sets up the **Nothing login** (greetd → Hyprland started locked by
  hyprlock) by default after asking; `--no-boot-lock` keeps the distribution's login screen.
  Shared helper `system/nothing-login.sh` (also used by Settings → Login screen).

### Fixed
- Buttons and menu entries that did nothing: the Hyprland session's PATH lacks `~/.local/bin`
  (login managers don't read `~/.bashrc`) — night-mode tile, Night Mode menu, launcher
  *Settings* entry, island network chip. PATH is now set in `hyprland.lua`, every internal call
  is absolute and launcher entries get absolute `Exec=` paths.
- Display settings now persist (nwg-displays writes old-syntax `monitors.conf`, ignored by the
  Lua config); VRR "fullscreen only" is no longer reset by saving.
- `make check` now verifies executable bits of every script, Python included.

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
