<div align="center">

# ● nothing — dotfiles

**A macOS‑style Hyprland desktop: frosted vibrant glass, SF Pro, Apple system colours, Light and Dark mode.**

[![CI](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml/badge.svg)](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml)
![Hyprland](https://img.shields.io/badge/Hyprland-0.56%2B%20·%20Lua-000000?logo=hyprland&logoColor=white)
![Arch](https://img.shields.io/badge/Arch%20%2F%20EndeavourOS-000000?logo=archlinux&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-007aff)](LICENSE)

EndeavourOS / Arch · Hyprland 0.56+ (Lua config) · Wayland · AMD

**[Guide](docs/GUIDE.md)** · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

</div>

> **New here?** Everything — installation, daily use, how the pieces fit together,
> customising and troubleshooting — is in **[docs/GUIDE.md](docs/GUIDE.md)**.

---

## Preview

| Desktop | Dynamic island (expanded) |
|---|---|
| ![desktop](assets/previews/desktop.png) | ![island](assets/previews/island.png) |

| Control center | Power menu | Lock screen |
|---|---|---|
| ![control](assets/previews/control-center.png) | ![power](assets/previews/power-menu.png) | ![lock](assets/previews/lockscreen.png) |

> Preview images are placeholders — drop your own screenshots into `assets/previews/`
> (`grim assets/previews/desktop.png`).

## Features

- **macOS menu bar** — one frosted bar: Tux system menu (About, Settings, Force Quit, Clear
  Clipboard History, Sleep, Restart, Shut Down, Lock, Log Out) · time + workspace dots in the
  centre · hover drawer (tray, CPU, memory) · network speed · Bluetooth · Wi‑Fi · battery ·
  clipboard · Control Center · date. It never shows which app, page or video is focused.
- **Light & Dark mode** — `Super` `Shift` `T`, the Control Center tile, Settings → Appearance or
  `nothing-theme toggle`: menu bar, Control Center, widgets, notifications, launcher, dock,
  Settings, kitty, GTK apps, Dolphin and other KDE/Qt apps, lock screen and wallpaper switch live.
- **Files like Finder** — `Super` `E` opens Nautilus with a translucent blurred sidebar when
  installed, otherwise Dolphin with macOS Dark / Light colour schemes, your accent, SF Pro,
  WhiteSur / Papirus icons, double-click to open, no menu bar.
- **Ten desktop widgets** — Weather, Clock / World Clock, Calendar & agenda, System rings,
  Storage, Batteries, Now Playing, Notes, Network, Focus Timer — small or medium. Drag them
  anywhere, click them, right-click for size / options / remove / add, or *Edit Widgets* for
  macOS-style remove badges and the **Add Widget** gallery. Also in Settings → Appearance and
  `nothing-shell widgets …`.
- **Traffic lights** — red / yellow / green on the left in GTK and libadwaita header bars;
  kitty, Dolphin and every other window get macOS title bars with the optional hyprbars plugin.
- **Appearance in Settings** — light / dark, eight Apple accent colours, window border, interface
  font (SF Pro, SF Pro Rounded, Inter, …), text and terminal font size, wallpaper gallery with
  add / delete, window opacity, corner radius, blur size and strength.
- **Notification banners** — top-right squircles under the menu bar with icon, bold title and
  round buttons, sliding in.
- **Security & privacy** — see [the Guide §4](docs/GUIDE.md#security--privacy): owner-only
  sockets and data files, no secrets on command lines, validated configs, nothing private on the
  lock screen or in the bar, password-manager clips kept out of clipboard history.
- **Dynamic island** (`nothing-shell`) — the workspace dots in the bar's centre; hover them for a
  panel with clock, weather, calendar, media and volume. Hover (or click) and it morphs into a panel: big clock, weather with a
  3‑day forecast, calendar, MPRIS media player (Spotify, Firefox, Chromium/YouTube, Netflix …)
  with album art, dot progress bar and controls, volume slider, network / Wi‑Fi / Bluetooth.
  A tiny animated dot equaliser shows while music plays; a pulsing red dot while recording.
  Hidden automatically when a window is fullscreen.
- **Control Center** — Wi‑Fi · Bluetooth · Microphone, Focus, Night Shift, Dark Mode, sound
  slider, live CPU graph, memory bar, CPU/GPU/SSD thermals, Notification Center history
  with per‑item dismiss and clear‑all, and power actions with two‑step confirm for
  destructive ones.
- **Power overlay** — full‑screen dim with five tiles and single‑key accelerators.
- **Settings app** (`Super` `I`) — Network, Bluetooth, Sound, Displays, Appearance, Night mode,
  Notifications, Keyboard & mouse, Power & lock, Login screen, Shortcuts, About. Every option is
  also a terminal command: `nothing-settings set appearance.rounding 12` (see the Guide).
- **Night mode** — warm screen via hyprsunset with a smooth fade, warmth presets and a
  schedule (presets or exact times). Settings, control-center tile or `Super` `Ctrl` `N`.
- **Nothing login** — boots straight into the Nothing lock screen instead of the standard
  login screen (greetd; on by default, switch in Settings → Login screen).
- **One lock screen** — hyprlock only: date above a large SF Pro Rounded clock, blur, battery/AC
  readout, now‑playing, keyboard‑layout chip, frosted password pill.
- **SF Pro everywhere** — `scripts/install-sf-fonts.sh` unpacks Apple's `SF-Pro.dmg` (and
  `SF-Mono.dmg`) from `~/Downloads`; without them fontconfig falls back to Inter / JetBrains Mono.
- **Austrian German, no dead keys** everywhere: Hyprland, hyprlock, login screen, TTY.
- **Works on any machine out of the box** — every screen at its preferred mode. Monitors, main
  screen and devices go in one git-ignored file, `~/.config/hypr/hyprland.local.lua`; start from
  `hypr/examples/` (dual-monitor desktop, laptop / 2-in-1).
- **Laptops** — battery in the bar, low-battery warnings, brightness keys, touchpad tap +
  3-finger workspace swipes, power key → power menu, Power Mode switch in Settings; on
  convertibles touchscreen + pen and auto-rotation in tablet mode.

## Install

```bash
git clone https://github.com/doveyQ/dotfiles ~/dotfiles
cd ~/dotfiles
make dry-run            # optional: preview every action
make install            # packages, keyboard/services, fonts, symlinks — asks before installing
```

The installer is idempotent — `make update` pulls and relinks.

| `make …` | |
|---|---|
| `install` | full install (`./install.sh`) |
| `links` | only relink configs, no sudo |
| `dry-run` | preview, change nothing |
| `check` | shellcheck · ruff · JSON(C) · `Hyprland --verify-config` (also run by CI) |
| `reload` | restart island, bars, popups, wallpaper, idle daemon |
| `update` | `git pull --ff-only` + relink |

| Flag | Effect |
|---|---|
| `--links-only` | only (re)link configs, no sudo |
| `--no-packages` / `--no-system` / `--no-fonts` | skip a stage |
| `--copy` | copy files instead of symlinking |
| `--dry-run` | print every action without changing anything |
| `-y` | don't ask before installing packages |
| `--no-boot-lock` | keep your distribution's login screen (default: ask, then use the Nothing lock screen) |
| `--restore-login` | go back to the previous login screen |

What it does:

1. **Packages** — everything in `packages/pacman.txt` via `pacman --needed`, plus
   `packages/aur.txt` via `yay` (bootstrapped if missing).
2. **System** — `localectl` keymap `at` / `nodeadkeys` (X11 + login screen) and
   `de-latin1-nodeadkeys` (TTY); enables `bluetooth` and `NetworkManager`; warns about other
   lockers (swaylock, swayidle, xss-lock) so hyprlock is the only one.
3. **Fonts** — unpacks Apple's SF fonts from `~/Downloads/SF-*.dmg` (download them from
   [developer.apple.com/fonts](https://developer.apple.com/fonts/)) into `~/.local/share/fonts/SF-Pro`;
   without them `hypr/themes/fonts.conf` maps SF Pro → Inter and SF Mono → JetBrains Mono.
4. **Configs** — existing `~/.config/<dir>` folders are moved to `~/.config-backup/<timestamp>/`,
   then symlinked to this repo. Helper commands go to `~/.local/bin`, launcher entries to
   `~/.local/share/applications`.
5. **Verify** — `Hyprland --verify-config`, Python and shell syntax checks; reloads the session
   if Hyprland is running.

Then log out and choose **Hyprland** on the login screen.

## Layout

```
dotfiles/
├── install.sh           idempotent installer (see --help)
├── Makefile             install · links · check · reload · update
├── docs/GUIDE.md        the full manual
├── scripts/check.sh     linters + config validation (make check, CI)
├── packages/            pacman.txt · aur.txt · laptop.txt (added when a battery is present)
├── settings/            Settings app + nothing-settings CLI
├── system/              login-screen helper + greetd template, laptop logind drop-in
├── system/logind/       laptops: power key → power menu
├── hypr/                → ~/.config/hypr
│   ├── hyprland.lua     loader (Hyprland ≥ 0.56 uses Lua, not hyprland.conf)
│   ├── conf/            monitors · autostart · input · look · rules · keybinds (.lua)
│   ├── themes/          mac-dark/ · mac-light/ (theme.lua · palette.css · palette.rasi · hyprlock.conf ·
│   │                    kitty.conf · wallpaper.jpg) · typography.css · fonts.conf (shared)
│   ├── theme            → themes/mac-dark|mac-light  (git-ignored; switched by nothing-theme)
│   ├── hyprlock.conf    lock screen
│   ├── hypridle.conf    idle → (dim) → lock → screens off → suspend
│   ├── examples/        machine files to copy to hyprland.local.lua (desktop, laptop)
│   ├── hyprpaper.conf
│   ├── wallpapers/
│   └── scripts/         record · battery · nowplaying · nothing-reload · brightness · autorotate
├── nothing-shell/       → ~/.config/nothing-shell   (island, Control Center, desktop widgets — Python/GTK3)
├── waybar/              → ~/.config/waybar   (the menu bar, scripts/)
├── swaync/              → ~/.config/swaync   (notification popups)
├── rofi/                → ~/.config/rofi     (launcher, power menu, cheat-sheet, scripts/)
├── kitty/               → ~/.config/kitty
├── nwg-dock-hyprland/   → ~/.config/nwg-dock-hyprland
├── fontconfig/          → ~/.config/fontconfig  (includes hypr/themes/fonts.conf: SF font fallbacks)
├── applications/        → ~/.local/share/applications  (Settings, Power Menu)
├── assets/previews/     README screenshots
└── .github/             CI workflow · issue & PR templates
```

## Keybindings

| Keys | Action |
|---|---|
| `Super` `Return` | Terminal (kitty) |
| `Super` `D` / `Super` `R` | App launcher |
| `Super` `I` | Settings |
| `Super` `N` | Control Center |
| `Super` `A` | Pin the dynamic island open |
| `Super` `Shift` `X` | Power menu — `P` power off · `R` reboot · `S` sleep · `L` lock · `E` log out · `Esc` |
| `Super` `L` | Lock |
| `Super` `Ctrl` `N` | Night mode on / off |
| `Super` `Shift` `T` | Light ↔ Dark mode |
| `Super` `Q` | Close window |
| `Super` `Space` | Toggle floating |
| `Super` `F` | Fullscreen |
| `Super` `V` | Clipboard history |
| `Super` `←↑→↓` | Focus (up/down crosses monitors) |
| `Super` `Shift` `←↑→↓` | Move window |
| `Super` `Ctrl` `←↑→↓` | Resize window |
| `Alt` `Tab` / `Super` `Tab` | Cycle windows / previous workspace |
| `Super` `1`–`0` · `Super` `Shift` `1`–`0` | Workspace · move window there |
| `Super` `Shift` `S` · `Shift` `Print` · `Super` `Shift` `Print` | Region → clipboard · full → ~/Pictures · record |
| `Super` `Shift` `R` | Reload the desktop |
| 3‑finger swipe | Previous / next workspace (touchpad and touchscreen) |
| Brightness keys · Power key | Brightness (with popup) · power menu — laptop |
| `Super` `F1` | Cheat‑sheet |

## Customising

- **Your machine** (monitors, main screen, touchpad, …): copy an example —
  `cp ~/.config/hypr/examples/laptop.lua ~/.config/hypr/hyprland.local.lua` — and edit it.
  It's git-ignored, so every computer keeps its own and `git pull` never conflicts.
  Bar on one screen only: `waybar/local.example.jsonc` → `~/.config/waybar/local.jsonc`.
- **Weather location**: `NOTHING_WEATHER_LOCATION=Vienna` — default is IP‑based.
- **Colours**: `hypr/themes/mac-dark/` and `mac-light/` define the same names. `palette.css`
  feeds every GTK surface (menu bar, island, Control Center, widgets, Settings app, dock,
  notifications), `palette.rasi` rofi, `theme.lua` Hyprland, `hyprlock.conf` the lock screen,
  `kitty.conf` the terminal. Apple system colours: blue `#007AFF` · green `#34C759` ·
  orange `#FF9500` · red `#FF3B30` · indigo `#5856D6` (dark mode uses Apple's brighter variants).
- **Fonts**: `hypr/themes/typography.css` (GTK) and the `$font_*` / `font-*` lines of the
  hyprlock / rofi palettes.
- **Light / Dark**: `nothing-theme toggle|light|dark|status` — or `Super` `Shift` `T`.
- **Window look** (border, rounding, shadows, blur, vibrancy, opacity): `hypr/conf/look.lua`;
  `borderless = true` in `theme.lua` drops the outlines and keeps only the shadows. Media and
  fullscreen windows stay opaque (`hypr/conf/rules.lua`).
- After editing nothing‑shell CSS: `nothing-shell reload-css`.

## Notes & troubleshooting

Short version below — the full table is in [the Guide §9](docs/GUIDE.md#9-troubleshooting).


- **Hyprland 0.56 dispatch syntax** — `hyprctl dispatch exit` no longer works; use Lua:
  `hyprctl dispatch 'hl.dsp.exit()'`, `hyprctl dispatch 'hl.dsp.dpms({ action = "off" })'`.
- **Locking** always goes `loginctl lock-session` → hypridle → hyprlock, so there is exactly one
  lock path. KDE's `kscreenlocker` only runs inside a Plasma session, never in Hyprland.
- **"Lockscreen app died" screen** (e.g. hyprlock crashed): switch to a TTY (`Ctrl+Alt+F3`),
  log in and run `hyprctl --instance 0 eval 'hl.clear_crashed_lockscreen()'`, then go back.
- **Bluetooth toggle does nothing** — the service is off: `sudo systemctl enable --now bluetooth`.
- **Logs**: `nothing-shell` prints to stderr; run it in a terminal (`nothing-shell quit; nothing-shell`).

## Contributing

PRs welcome — run `make check`, follow [Conventional Commits](https://www.conventionalcommits.org/),
see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Apple's SF fonts are not included and keep Apple's license.

## Credits

Inter by Rasmus Andersson · JetBrains Mono ·
Hyprland and the hypr* ecosystem · Waybar · SwayNC · Rofi · kitty · weather from [wttr.in](https://wttr.in).
