# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security
- Wi-Fi passwords are passed to nmcli on stdin, no longer on the command line.
- nothing-shell's socket is 0600 and checks the peer UID; requests are size-capped.
- Settings, notification history, clipboard history, widget layout and weather cache are
  written owner-only through private temp files; install.sh tightens existing ones.
- Lua serialisation escapes all control characters; wallpaper paths are validated before
  they reach hyprpaper; autorotate no longer falls back to /tmp and validates its state.
- clipboard history capped at 200 entries (password-manager clips are never stored).
- The lock screen no longer shows the playing media; the menu bar no longer shows the focused
  app or window title.

### Changed — macOS redesign
- Menu bar: Tux replaces the Apple logo; the time sits in the centre next to the workspace
  dots, the date on the right; neutral now-playing indicator and album-art placeholder.
- **macOS look** in a **Light** and a **Dark** mode: frosted vibrant glass (Hyprland blur 8×4,
  vibrancy 0.35, explicit `glass-…` layer rules for the bar, island, Control Center, widgets,
  notifications, rofi, dock and `gtk-layer-shell`), Apple system colours, hairline window
  edges, deep soft shadows, 0.96 / 0.90 window opacity (media and fullscreen stay opaque).
- **Light / Dark switch**: `nothing-theme toggle|light|dark|status`, `Super+Shift+T`, a Control
  Center tile and Settings → Appearance. Swaps `hypr/theme` → `themes/mac-dark|mac-light`
  (now git-ignored) and live-reloads Hyprland, Waybar, SwayNC, nothing-shell, kitty, the dock,
  GTK `color-scheme` and the wallpaper.
- **Menu bar**: one continuous bar — Apple menu (About, Settings, Force Quit, Sleep, Restart,
  Shut Down, Lock, Log Out), bold app name, window title, workspace dots, hover drawer, network
  speed, Bluetooth, Wi-Fi, battery, clipboard, Control Center, `Fri 23 Oct  1:07 PM`.
- **Control Center** rebuilt like macOS: connectivity module, Focus, Night Shift, Dark Mode,
  sound slider, CPU graph, memory bar, thermals, Notification Center cards, power buttons.
- **Desktop widgets** moved from a second Waybar into nothing-shell and drawn with cairo:
  Weather (sky gradients), analog Clock, Calendar, System (activity rings).
- **SF Pro** typography (`hypr/themes/typography.css`): `scripts/install-sf-fonts.sh` unpacks
  Apple's `SF-*.dmg` with 7-Zip; `hypr/themes/fonts.conf` falls back to Inter / JetBrains Mono.
- Settings app: translucent window, frosted sidebar, traffic lights, title-case headings.
- Spotlight-style launcher, macOS lock screen, Terminal-like kitty colours, new dark / light
  wallpapers. `hyprland.lua` is a loader for `hypr/conf/{monitors,autostart,input,look,rules,keybinds}.lua`.

### Added
- **Customisable desktop widgets**: drag anywhere, click actions, small / medium sizes, analog
  / digital clock, add / remove (right-click, Edit Widgets mode with badges, Settings →
  Appearance, `nothing-shell widgets …`), layout saved per machine in
  `~/.config/nothing/widgets.json` and validated on load.
- Tux system menu entry *Clear Clipboard History*.
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
