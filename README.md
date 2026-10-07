<div align="center">

# ● nothing — dotfiles

**A Nothing OS–inspired Hyprland desktop: deep blacks, crisp whites, dot‑matrix type and one red accent.**

[![CI](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml/badge.svg)](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml)
![Hyprland](https://img.shields.io/badge/Hyprland-0.56%2B%20·%20Lua-000000?logo=hyprland&logoColor=white)
![Arch](https://img.shields.io/badge/Arch%20%2F%20EndeavourOS-000000?logo=archlinux&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-d71921)](LICENSE)

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
> (`grim -o DP-2 assets/previews/desktop.png`).

## Features

- **Dynamic island** (`nothing-shell`) — compact pill with workspace dots, weather and a
  dot‑matrix clock. Hover (or click) and it morphs into a panel: big clock, weather with a
  3‑day forecast, calendar, MPRIS media player (Spotify, Firefox, Chromium/YouTube, Netflix …)
  with album art, dot progress bar and controls, volume slider, network / Wi‑Fi / Bluetooth.
  A tiny animated dot equaliser shows while music plays; a blinking red dot while recording.
  Hidden automatically when a window is fullscreen.
- **Control center** — live dot‑matrix CPU history graph, RAM bar, CPU/GPU/SSD thermals
  (tiles turn red when hot), Wi‑Fi / Bluetooth / Silent / Mic toggles, notification history
  with per‑item dismiss and clear‑all, and power actions with two‑step confirm for
  destructive ones.
- **Power overlay** — full‑screen dim with five tiles and single‑key accelerators.
- **Settings hub** — Wi‑Fi, Bluetooth, Sound, Displays, Appearance, Keyboard, Wallpaper,
  DND, idle/lock, configs, keybinding cheat‑sheet. Also in the app launcher as *Settings*.
- **Night mode** — warm screen via hyprsunset with a smooth fade, warmth presets and a
  schedule (presets or custom times). Settings hub, control-center tile or `Super` `Ctrl` `N`.
- **Boot lock** (optional) — boot straight into the Nothing lock screen instead of the KDE
  login screen: `./install.sh --boot-lock`.
- **One lock screen** — hyprlock only: giant Ndot clock, blur, battery/AC readout,
  now‑playing, keyboard‑layout chip, red‑accented password pill.
- **Austrian German, no dead keys** everywhere: Hyprland, hyprlock, login screen, TTY.
- Dual monitor: workspaces 1–5 on the bottom 144 Hz screen (DP‑2), 6–10 on the top (HDMI‑A‑1).

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
| `--boot-lock` | boot into hyprlock (greetd autologin) instead of the KDE login screen |
| `--restore-login` | undo `--boot-lock` |

What it does:

1. **Packages** — everything in `packages/pacman.txt` via `pacman --needed`, plus
   `packages/aur.txt` via `yay` (bootstrapped if missing).
2. **System** — `localectl` keymap `at` / `nodeadkeys` (X11 + login screen) and
   `de-latin1-nodeadkeys` (TTY); enables `bluetooth` and `NetworkManager`; warns about other
   lockers (swaylock, swayidle, xss-lock) so hyprlock is the only one.
3. **Fonts** — Nothing's Ndot 55/57, NType 82 from
   [xeji01/nothingfont](https://github.com/xeji01/nothingfont) into `~/.local/share/fonts/nothing`.
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
├── packages/            pacman.txt · aur.txt
├── system/greetd/       boot-lock login config (opt-in, --boot-lock)
├── hypr/                → ~/.config/hypr
│   ├── hyprland.lua     main config (Hyprland ≥ 0.56 uses Lua, not hyprland.conf)
│   ├── hyprlock.conf    lock screen
│   ├── hypridle.conf    idle → lock → screens off → suspend
│   ├── hyprpaper.conf
│   ├── wallpapers/
│   └── scripts/         record · battery · nowplaying · nothing-reload
├── nothing-shell/       → ~/.config/nothing-shell   (island + control center, Python/GTK3)
├── waybar/              → ~/.config/waybar   (logo + status pill, desktop widgets, scripts/)
├── swaync/              → ~/.config/swaync   (notification popups)
├── rofi/                → ~/.config/rofi     (launcher, settings hub, power menu, scripts/)
├── kitty/               → ~/.config/kitty
├── nwg-dock-hyprland/   → ~/.config/nwg-dock-hyprland
├── applications/        → ~/.local/share/applications  (Settings, Power Menu)
├── assets/previews/     README screenshots
└── .github/             CI workflow · issue & PR templates
```

## Keybindings

| Keys | Action |
|---|---|
| `Super` `Return` | Terminal (kitty) |
| `Super` `D` / `Super` `R` | App launcher |
| `Super` `I` | Settings hub |
| `Super` `N` | Control center |
| `Super` `A` | Pin the dynamic island open |
| `Super` `Shift` `X` | Power menu — `P` power off · `R` reboot · `S` sleep · `L` lock · `E` log out · `Esc` |
| `Super` `L` | Lock |
| `Super` `Ctrl` `N` | Night mode on / off |
| `Super` `Q` | Close window |
| `Super` `Space` | Toggle floating |
| `Super` `F` | Fullscreen |
| `Super` `V` | Clipboard history |
| `Super` `←↑→↓` | Focus (up/down crosses monitors) |
| `Super` `Shift` `←↑→↓` | Move window |
| `Super` `Ctrl` `←↑→↓` | Resize window |
| `Alt` `Tab` / `Super` `Tab` | Cycle windows / previous workspace |
| `Super` `1`–`0` · `Super` `Shift` `1`–`0` | Workspace · move window there |
| `Print` · `Shift` `Print` · `Super` `Shift` `Print` | Region → clipboard · full → ~/Pictures · record |
| `Super` `Shift` `R` | Reload the desktop |
| `Super` `F1` | Cheat‑sheet |

## Customising

- **Main monitor** for the island / dock: `NOTHING_OUTPUT=DP-2` (env) — default `DP-2`.
- **Weather location**: `NOTHING_WEATHER_LOCATION=Vienna` — default is IP‑based.
- **Colours**: `nothing-shell/style.css`, `waybar/style.css`, `rofi/nothing.rasi`, `kitty/kitty.conf`
  all share the palette `#000 · #141414 · #1e1e1e@80% · #fff · #d71921`.
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

[MIT](LICENSE). The Nothing fonts are not included and keep their own license.

## Credits

Nothing fonts by Nothing Technology (via [xeji01/nothingfont](https://github.com/xeji01/nothingfont)) ·
Hyprland and the hypr* ecosystem · Waybar · SwayNC · Rofi · kitty · weather from [wttr.in](https://wttr.in).
