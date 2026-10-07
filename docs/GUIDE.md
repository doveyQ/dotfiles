# The Guide

Everything you need to know to install, use, understand, customise and fix this desktop.
New here? Read **1 → 3**. Changing things? **5 → 7**. Something broken? **9**.

- [1. What this is](#1-what-this-is)
- [2. Installing](#2-installing)
- [3. Daily use](#3-daily-use)
- [4. How it works](#4-how-it-works)
- [5. Customising](#5-customising)
- [6. Hyprland 0.56 & Lua — a primer](#6-hyprland-056--lua--a-primer)
- [7. Maintaining the repo](#7-maintaining-the-repo)
- [8. Uninstalling](#8-uninstalling)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Known limitations & gotchas](#10-known-limitations--gotchas)

---

## 1. What this is

A complete Hyprland desktop modelled on **Nothing OS**: deep black surfaces, white type,
dot-matrix numerals (the Ndot fonts) and a single red accent that always means
*live, active or dangerous*.

```
┌───────────────────────────────── main screen ────────────────────────────────────┐
│ [tux]             ⣿ ▬ · · · ·  ☀ 15°  11:32             [rec 📋 CPU RAM 🔔 ⏻]   │  ← top bar
│  ╰ waybar            ╰ nothing-shell: dynamic island          ╰ waybar status pill│
│                                                                                  │
│ ┌ weather ┐                                                   MON, 07 OCT        │
│ │ cards   │   (desktop widgets: waybar on the background layer)  12:27  ← Ndot    │
│ └─────────┘                                                   CPU ●●○○  RAM ●●○  │
│                                                                                  │
│                      ┌──────── nwg-dock (auto-hide) ────────┐                    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Component | Role | Config |
|---|---|---|
| **Hyprland** | compositor, windows, workspaces, keybinds | `hypr/hyprland.lua` |
| **nothing-shell** | dynamic island + control center (Python/GTK3, layer-shell) | `nothing-shell/` |
| **Waybar** (×2) | logo + status pill · desktop widgets | `waybar/` |
| **SwayNC** | notification *popups* and Do-Not-Disturb | `swaync/` |
| **Rofi** | app launcher, settings hub, power menu, clipboard, cheat-sheet | `rofi/` |
| **hyprlock** | the one and only lock screen | `hypr/hyprlock.conf` |
| **hypridle** | idle timeline, answers every lock request | `hypr/hypridle.conf` |
| **hyprpaper** | wallpaper | `hypr/hyprpaper.conf` |
| **nwg-dock** | auto-hiding dock on the main screen | `nwg-dock-hyprland/` |
| **kitty** | terminal | `kitty/kitty.conf` |

**Monitors.** Out of the box every screen runs at its preferred mode and the island, bar and
dock use the primary one. Your own layout (which screen is *main*, positions, refresh rates,
which workspaces go where) lives in a git-ignored machine file — see §2 *Your machine*.
`Super`+arrows move focus across screens.

---

## 2. Installing

### Fresh machine (EndeavourOS / Arch)

```bash
git clone https://github.com/doveyQ/dotfiles ~/dotfiles
cd ~/dotfiles
make dry-run      # optional: see exactly what will happen
make install      # = ./install.sh
```

Then **log out → choose “Hyprland” on the login screen** (not “Hyprland (uwsm-managed)”).

`install.sh` is idempotent — run it as often as you like. It:

1. installs `packages/pacman.txt` (and `packages/aur.txt` via yay, if non-empty),
2. sets the keyboard system-wide to **Austrian German, no dead keys**, enables
   `bluetooth` + `NetworkManager`, warns about competing lockers,
3. downloads the Nothing fonts to `~/.local/share/fonts/nothing`,
4. **moves your existing configs to `~/.config-backup/<timestamp>/`** and symlinks
   `~/.config/<dir>` → `~/dotfiles/<dir>`, commands → `~/.local/bin`, launcher entries →
   `~/.local/share/applications`,
5. verifies everything and reloads the session if Hyprland is running.

| Flag | Meaning |
|---|---|
| `--links-only` | only the symlinks (no sudo) — `make links` |
| `--no-packages` · `--no-system` · `--no-fonts` | skip a stage |
| `--copy` | copy instead of symlink (no live link to the repo) |
| `--dry-run` | print actions, change nothing |
| `-y` | no confirmation for pacman / yay |

Because configs are **symlinks**, editing `~/.config/hypr/hyprland.lua` *is* editing the repo.
`git status` in `~/dotfiles` shows every change you made.

### Boot straight into the lock screen (optional)

By default the login screen at boot is your display manager's (on this machine KDE's
*Plasma Login*), which can't look like hyprlock. To make the **Nothing lock screen the
first thing you see**:

```bash
./install.sh --boot-lock        # installs greetd + tuigreet, takes effect at next boot
./install.sh --restore-login    # back to the previous login screen
```

How it works: greetd logs you in automatically and starts
`start-hyprland -- --locked-cmd hyprlock`, so Hyprland comes up **already locked** — no
desktop frame is ever shown before hyprlock, and if hyprlock failed the session would stay
locked (see §9). After you log out you get a minimal text greeter (tuigreet; `F3` picks
another session, e.g. Plasma).

Trade-off: the password is checked by hyprlock *after* login, so PAM modules that unlock
things at login (KWallet / GNOME Keyring) don't run — apps using them will ask for the
wallet password once. Full-disk encryption is the right protection for data at rest
either way.

### Your machine (monitors, laptop, devices)

The repo is a neutral default; everything that belongs to **one computer** goes in
`~/.config/hypr/hyprland.local.lua`. It's git-ignored (`*.local.lua`), so each machine keeps its
own copy, and you can `git pull` / push the shared config without touching it. Start from an
example:

```bash
cp ~/.config/hypr/examples/desktop-dual-monitor.lua ~/.config/hypr/hyprland.local.lua   # two screens
cp ~/.config/hypr/examples/laptop.lua               ~/.config/hypr/hyprland.local.lua   # laptop / 2-in-1
```

The file returns a table; every field is optional:

```lua
return {
    main      = "DP-2",                                   -- island, bar, dock, popups, recorder
    monitors  = { { output = "DP-2", mode = "1920x1080@144", position = "0x0", scale = 1 } },
    workspace = function(i) return "DP-2" end,            -- monitor for workspace i
    setup     = function()                                -- runs last: override anything
        hl.config({ input = { touchpad = { natural_scroll = true } } })
        hl.bind("SUPER + T", hl.dsp.exec_cmd("thunar"))
    end,
}
```

Names come from `hyprctl monitors` and `hyprctl devices`. `main` is exported as
`NOTHING_OUTPUT`; `NOTHING_WORKSPACES` (set it in `setup` with `hl.env`) is how many workspace
dots the island shows (default 10). Hyprland reloads on save; `Super` `Shift` `R` restarts the
rest. Mistakes appear in the red error bar.

**Waybar** shows on every screen unless you limit it: copy `waybar/local.example.jsonc` to
`~/.config/waybar/local.jsonc` (also git-ignored) and set `"output"`. SwayNC follows the
focused screen.

**Laptops** — `install.sh` notices the battery and also installs `packages/laptop.txt`
(brightnessctl, iio-sensor-proxy, power-profiles-daemon) plus a logind drop-in so the power key
opens the power menu instead of switching off. The shared config already handles brightness
keys (with a popup), tap-to-click, 3-finger workspace swipes, backlight dimming 30 s before the
lock, low-battery warnings (20 / 10 %) and the battery in the status pill (click → Power Mode).
`examples/laptop.lua` adds the machine-specific part: natural scrolling, touchpad acceleration,
touchscreen + pen mapped to the panel and, on convertibles, auto-rotation **only in tablet
mode** (`scripts/autorotate.sh`, triggered by the tablet-mode switch).

**Other hardware** — keyboard: `INPUT` section of `hyprland.lua` + `localectl` (see 5).
NVIDIA: remove the `LIBVA_DRIVER_NAME` line and follow the Hyprland wiki's NVIDIA page.

---

## 3. Daily use

### The dynamic island (top centre)

*Idle:* workspace dots (the white pill is the active one), weather, dot-matrix clock.
A tiny animated **dot equaliser** appears while media plays; a **blinking red dot** while
recording the screen; a red speaker if audio is muted.

| Do | Result |
|---|---|
| hover | expands after ~0.15 s, collapses ~0.5 s after you leave |
| left-click the pill / `Super` `A` | pin it open (click again to close) |
| right-click | open the control center |
| scroll on it | previous / next workspace |
| click a workspace dot | jump to that workspace |

Expanded you get: big clock & date · weather now + 3-day forecast · calendar ·
**media player** (follows whichever player last started playing — Spotify, Firefox,
Chromium/YouTube, Netflix, mpv, … — art, title, artist, dot progress bar, ⏮ ⏯ ⏭, and a
⇄ button when several players are open) · volume slider + mute · network chip (opens Wi-Fi
settings) · Wi-Fi and Bluetooth toggles.

It hides itself while a window is fullscreen on the main screen.

### Control center — `Super` `N` (or click CPU / RAM / 🔔 in the status pill)

Live CPU history as a dot matrix (newest column red), RAM, CPU/GPU/SSD temperatures (tile
turns red when hot), toggles for **Wi-Fi · Bluetooth · Silent (DND) · Mic**, notification
history (✕ to dismiss, **CLEAR** for all) and power buttons. **Exit / Reboot / Off ask
twice** — the button turns red and says *AGAIN?* for 2.6 s.
Closes with `Esc`, `Super` `N`, or when the pointer leaves it.

### Power menu — `Super` `Shift` `X` (or click ⏻)

| Key | Action |
|---|---|
| `P` | power off |
| `R` | reboot |
| `S` | sleep (locks first) |
| `L` | lock |
| `E` | log out of Hyprland |
| `Esc` / `Q` | cancel |

Arrow keys + `Enter` and the mouse work too.

### Settings hub — `Super` `I` (or search “Settings” in the launcher, or right-click the tux)

Wi-Fi & Network (nmtui) · Bluetooth (blueman) · Sound (pavucontrol) · Displays (nwg-displays) ·
Appearance (nwg-look: GTK theme, icons, cursor) · Keyboard · Wallpaper picker ·
Do Not Disturb · Idle & Sleep · Lock Screen · Hyprland Config · Keybindings · Reload Desktop ·
KDE System Settings. Each entry also works directly: `nothing-settings wifi`, `… audio`, etc.

### Night mode

Warms the screen colour (hyprsunset) with a smooth ~1 s fade. A small moon appears in the
island while it is on.

| Where | How |
|---|---|
| keys | `Super` `Ctrl` `N` toggles |
| control center | **NIGHT** tile |
| settings hub | **Night Mode** → on/off · warmth · schedule |
| terminal | `nothing-night on\|off\|toggle`, `nothing-night temp 3500`, `nothing-night schedule 21:30 06:45`, `nothing-night schedule off`, `nothing-night status` |

**Warmth presets:** 5500 K subtle · 4500 warm · **4000 default** · 3500 very warm · 2800 candle.
**Schedule presets:** Evening 20:00→07:00 · Late 22:00→06:30 · Long 19:00→08:00, or *Custom times…*
(24-hour `HH:MM`; windows may cross midnight). A manual toggle wins until the schedule's next
switch — e.g. turning it off at 21:00 keeps it off until 07:00, then the schedule resumes.
You get a quiet notification when the schedule switches.

State is machine-local: `~/.local/state/nothing/night.json`.

### Locking & idle

`Super` `L`, the power menu and the control center all call `loginctl lock-session`.
hypridle answers that with hyprlock. The idle timeline:

| Time idle | What happens |
|---|---|
| 14:30 | notification “Locking in 30 seconds” |
| 15:00 | lock |
| 15:30 | screens off (any input wakes them) |
| 60:00 | suspend |

Video playback and calls inhibit idle. Media keys keep working on the lock screen.
The lock screen shows the current keyboard layout — type your password with that layout.

### Notifications

Popups appear top-right (SwayNC). History lives in the control center. The bell gets a red
dot when there is history; `Super` `Shift` `N` (or right-click the bell) toggles DND.

### Screenshots, recording, clipboard

| Keys | Action |
|---|---|
| `Print` | select region → clipboard |
| `Shift` `Print` | whole screen → `~/Pictures/` |
| `Super` `Shift` `Print` | start/stop recording (select region; `Esc` = whole main screen) → `~/Videos/` |
| `Super` `V` | clipboard history |

### All keybindings

`Super` `F1` shows them anywhere. Full table in the [README](../README.md#keybindings).

---

## 4. How it works

### Startup

Hyprland reads `hypr/hyprland.lua`; the `hyprland.start` hook launches, in order:
polkit agent → hyprpaper → **hypridle** → hyprsunset → swaync → **nothing-shell** → waybar (bar) →
waybar (desktop widgets) → nwg-dock → clipboard watcher.

### nothing-shell

One Python process (`~/.local/bin/nothing-shell` → `nothing-shell/nothing-shell.py`) with two
GTK3 layer-shell windows:

- `nothing-island` — **overlay** layer (so it sits above Waybar's full-width surface),
  anchored top-centre. Expansion is a two-step morph: the pill widens (cubic ease-out, own
  frame-clock animation), then a `GtkRevealer` slides the panel down; collapsing reverses it.
- `nothing-control` — top layer, anchored top-right. Its slide-in is a Hyprland layer
  animation (`layer_rule … animation = "slide right"`).

It talks to the system through: **Hyprland's event socket** (`.socket2.sock` — workspace,
window and fullscreen events), **Playerctl** (MPRIS), `wpctl` (PipeWire volume), `nmcli`,
`bluetoothctl`, `swaync-client`, `/proc` and `/sys/class/hwmon` (CPU, RAM, temps), and the
weather cache written by `waybar/scripts/weather.py` (wttr.in, refreshed every 15 min).

**Notification history** is collected passively: nothing-shell becomes a D-Bus *monitor* for
`org.freedesktop.Notifications.Notify` calls, so SwayNC remains the actual notification
server. History is stored in `~/.cache/nothing-shell/notifications.json` (max. 60).

**IPC** — a Unix socket at `$XDG_RUNTIME_DIR/nothing-shell.sock`:

```bash
nothing-shell                         # start the daemon (no-op if already running)
nothing-shell island  open|close|toggle
nothing-shell control open|close|toggle
nothing-shell notif-status            # JSON for the waybar bell
nothing-shell notif-clear
nothing-shell reload-css              # after editing nothing-shell/style.css
nothing-shell quit
```

### The lock pipeline

```
Super+L / power menu / control center / sleep / 15 min idle
                     │
           loginctl lock-session          (systemd-logind emits "Lock")
                     │
                 hypridle                 lock_cmd = pidof hyprlock || hyprlock
                     │
                 hyprlock                 ext-session-lock — Hyprland keeps the session
                                          locked even if hyprlock dies (see §9)
```

Before suspend, hypridle locks first and holds a sleep inhibitor until hyprlock is up
(`inhibit_sleep = 3`), so the desktop never flashes on resume.

### Keyboard layout, four layers

| Where | Set by |
|---|---|
| Hyprland (all apps) | `hyprland.lua` → `input.kb_layout = "at"`, `kb_variant = "nodeadkeys"` |
| hyprlock | inherits Hyprland's keymap; the layout chip shows it |
| login screen (SDDM / Plasma Login) | `localectl set-x11-keymap at pc105 nodeadkeys` |
| TTY (`Ctrl+Alt+F3`) | `localectl set-keymap de-latin1-nodeadkeys` |

### Waybar signals

Scripts poke Waybar instead of polling fast: `pkill -RTMIN+8 waybar` refreshes the recording
dot, `-RTMIN+9` the notification bell.

### Files outside the repo

| Path | What |
|---|---|
| `~/.cache/nothing-weather.json` | weather cache |
| `~/.cache/nothing-shell/` | notification history, album-art cache |
| `~/.local/state/nothing/night.json` | night-mode state and schedule |
| `/etc/greetd/config.toml` | only with `--boot-lock` (template: `system/greetd/config.toml`) |
| `/etc/systemd/logind.conf.d/10-nothing-laptop.conf` | laptops: power key → power menu |
| `$XDG_RUNTIME_DIR/nothing-rotate/` | auto-rotation state (convertibles) |
| `hypr/hyprland.local.lua`, `waybar/local.jsonc` | your machine files — inside the repo folder, git-ignored |
| `~/.local/share/fonts/nothing/` | Ndot / NType fonts |
| `~/.config-backup/<timestamp>/` | your configs from before the first install |

---

## 5. Customising

| I want to change… | Edit |
|---|---|
| colours | `nothing-shell/style.css`, `waybar/style.css`, `waybar/desktop.css`, `rofi/*.rasi`, `swaync/style.css`, `kitty/kitty.conf`, `hypr/hyprlock.conf` (all share one palette) |
| gaps, borders, rounding, blur, animations | `hypr/hyprland.lua` → LOOK AND FEEL |
| keybindings | `hypr/hyprland.lua` → KEYBINDINGS (+ `rofi/scripts/keybinds.sh` cheat-sheet + README) |
| autostart | `hypr/hyprland.lua` → `hl.on("hyprland.start", …)` |
| idle / lock / suspend times | `hypr/hypridle.conf` |
| lock-screen look | `hypr/hyprlock.conf` |
| wallpaper | Settings hub → Wallpaper (drop images into `hypr/wallpapers/`) |
| weather location | `export NOTHING_WEATHER_LOCATION=Vienna` (e.g. via `hl.env(...)` in hyprland.lua) |
| monitors, main screen for the island, touchpad, per-machine binds | `~/.config/hypr/hyprland.local.lua` (§2 *Your machine*) |
| settings-hub entries | `rofi/scripts/settings.sh` — add a `label|key` line and a `case` branch |
| island content | `nothing-shell/nothing-shell.py` → `Island._build_panel()` |

**Apply changes:** Hyprland reloads `hyprland.lua` automatically on save; everything else:
`make reload` or `Super` `Shift` `R`. Always run `make check` before committing.

**Machine-specific tweaks** never go into the shared files — put them in
`~/.config/hypr/hyprland.local.lua` (its `setup()` runs last and can override anything) and
`~/.config/waybar/local.jsonc`. Both are git-ignored; see §2 *Your machine*.

**Fonts.** Ndot is used for numerals and headings. In **Pango font strings** (hyprlock, rofi)
write `Ndot 57,` with a trailing comma — otherwise Pango reads `57` as the size. In GTK/Waybar
CSS (`font-family: "Ndot 57"`) no comma is needed.

---

## 6. Hyprland 0.56 & Lua — a primer

Hyprland 0.56 replaced `hyprland.conf` with **`hyprland.lua`**. Old snippets from the
internet will not work as-is.

```lua
hl.config({ general = { gaps_in = 8 } })              -- options
hl.bind("SUPER + Q", hl.dsp.window.close())           -- keybind → dispatcher
hl.bind("SUPER + B", hl.dsp.exec_cmd("firefox"))
hl.window_rule({ name = "x", match = { class = "^pavucontrol$" }, float = true })
hl.on("hyprland.start", function() hl.exec_cmd("waybar") end)
```

From the shell, `hyprctl dispatch` takes a **Lua expression**:

```bash
hyprctl dispatch 'hl.dsp.exit()'                         # NOT: hyprctl dispatch exit
hyprctl dispatch 'hl.dsp.focus({ workspace = 3 })'
hyprctl dispatch 'hl.dsp.dpms({ action = "off" })'
hyprctl eval 'hl.config({ decoration = { rounding = 0 } })'   # live, until next reload
hyprctl repl                                             # interactive Lua prompt
```

`hyprctl keyword …` is gone (“can't work with non-legacy parsers”).
Validate before you reload: `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua` —
it is strict and names unknown keys. API reference: `/usr/share/hypr/stubs/hl.meta.lua`.

---

## 7. Maintaining the repo

```bash
make help        # list tasks
make check       # lint shell (shellcheck), python (ruff), JSON/JSONC, verify hyprland.lua
make reload      # restart island, bars, popups, wallpaper, idle daemon
make update      # git pull --ff-only + relink
```

- CI (`.github/workflows/ci.yml`) runs `make check` on every push and PR.
- Commits follow **Conventional Commits** (`feat(island): …`, `fix(hyprlock): …`) — see
  [CONTRIBUTING](../CONTRIBUTING.md).
- Record user-visible changes in [CHANGELOG](../CHANGELOG.md) under *Unreleased*; on release
  move them under a version and tag it: `git tag -a v1.1.0 -m "v1.1.0" && git push --tags`.
- Screenshots for the README go to `assets/previews/` (`grim assets/previews/desktop.png`)
  — check them for private windows before committing.

---

## 8. Uninstalling

```bash
# remove the links created by install.sh
for d in hypr waybar swaync rofi kitty nwg-dock-hyprland nothing-shell; do
  [ -L ~/.config/$d ] && rm ~/.config/$d
done
rm -f ~/.local/bin/nothing-{shell,settings,power,keybinds,reload}
rm -f ~/.local/share/applications/nothing-{settings,power}.desktop

# restore your previous configs
cp -r ~/.config-backup/<timestamp>/* ~/.config/
```

Packages are left installed; remove them with `sudo pacman -Rns …` if you want.

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| Red error bar at the top | `hyprctl configerrors`, or `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua` |
| Island / control center missing | `nothing-shell quit; nothing-shell` in a terminal — errors are printed there |
| Island on the wrong monitor | `main` in `hyprland.local.lua` (§2 *Your machine*); monitor names: `hyprctl monitors` |
| Laptop: brightness keys do nothing | `pacman -Q brightnessctl`; `brightnessctl set 50%` in a terminal |
| Laptop: no auto-rotation in tablet mode | `hyprctl devices` must list the switch `HP WMI hotkeys`; `monitor-sensor --accel` must print orientations; screen stuck rotated: `~/.config/hypr/scripts/autorotate.sh tablet off` |
| Bluetooth toggle does nothing, `bluetoothctl` hangs | `sudo systemctl enable --now bluetooth` |
| Wrong keys / dead keys on the login screen or TTY | `sudo localectl set-x11-keymap at pc105 nodeadkeys` · `sudo localectl set-keymap --no-convert de-latin1-nodeadkeys` |
| **“Oopsie daisy … lockscreen app died”** | `Ctrl+Alt+F3`, log in, `hyprctl --instance 0 eval 'hl.clear_crashed_lockscreen()'`, back with `Ctrl+Alt+F1/F2`. Never kill hyprlock to “unlock”. |
| Login screen at boot looks like KDE | that's the display manager — `./install.sh --boot-lock` (see §2) |
| Night mode does nothing | `pacman -Q hyprsunset`; `pgrep hyprsunset`; `nothing-night status` |
| Screens stay black after idle | press a key / move the mouse; or `hyprctl dispatch 'hl.dsp.dpms({ action = "on" })'` |
| Weather shows `--` | offline or wttr.in down; `~/.config/waybar/scripts/weather.py bar` to test |
| No album art | the player doesn't publish `mpris:artUrl` (common for browser tabs) — a dot placeholder is shown |
| Icons show as □ | Nerd fonts missing: `sudo pacman -S ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols` |
| Dot-matrix text shows as a normal font | `fc-list \| grep Ndot` — rerun `./install.sh --no-packages --no-system` |
| A rofi menu shows raw CSS as text | a `.rasi` line with two quoted strings — keep one quoted value per line |
| `hyprctl dispatch exit` → “')' expected near …” | 0.56 syntax: `hyprctl dispatch 'hl.dsp.exit()'` |

Logs: Hyprland `~/.local/share/hyprland/` / `$XDG_RUNTIME_DIR/hypr/*/hyprland.log`,
user services `journalctl --user -b`.

---

## 10. Known limitations & gotchas

- **SwayNC sliders** (0.12.6) never call their `cmd_getter`, so live CPU/RAM bars can't live in
  SwayNC — that's why the control center is part of nothing-shell.
- **GTK3 revealers on re-mapped layer surfaces** stall (frame clock never ticks), so the control
  center animates via Hyprland's layer animation instead.
- **`grep -q` inside pipelines with `set -o pipefail`** reports failure on a match (SIGPIPE to the
  writer). The scripts use `grep … >/dev/null` instead.
- **GTK3 has no monitor connector names** — nothing-shell maps `NOTHING_OUTPUT` to a GDK monitor
  by matching positions from `hyprctl monitors`.
- **Battery** — desktops show “AC POWER” on the lock screen; laptops get a dot bar.
- **KDE Plasma** stays installed and selectable on the login screen; its own lock screen
  (`kscreenlocker`) only ever runs inside a Plasma session.
