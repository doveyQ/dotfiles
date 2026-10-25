<div align="center">

# dotfiles — a macOS‑style Hyprland desktop

**Frosted vibrant glass, SF Pro, Apple system colours, Light & Dark mode — on Hyprland.**

[![CI](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml/badge.svg)](https://github.com/doveyQ/dotfiles/actions/workflows/ci.yml)
![Hyprland](https://img.shields.io/badge/Hyprland-0.56%2B%20·%20Lua-000000?logo=hyprland&logoColor=white)
![Arch](https://img.shields.io/badge/Arch%20%2F%20EndeavourOS-000000?logo=archlinux&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-007aff)](LICENSE)

EndeavourOS / Arch · Hyprland 0.56+ (Lua config) · Wayland · AMD

**[Guide](docs/GUIDE.md)** · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

Made by [doveyQ](https://github.com/doveyQ) · co-authored with **Claude** (Anthropic) via
[Claude Code](https://claude.com/claude-code)

</div>

> **New here?** Everything — installation, daily use, how the pieces fit together,
> customising, security and troubleshooting — is in **[docs/GUIDE.md](docs/GUIDE.md)**.

---

> **Screenshots:** none are committed yet — add yours to `assets/previews/`
> (`grim assets/previews/desktop.png`). Check them for personal data (notifications, network
> names, open windows) before you push.

## Features

**Desktop**

- **Menu bar** — one frosted bar: Tux system menu (About, Settings, Force Quit, Clear Clipboard
  History, Sleep, Restart, Shut Down, Lock, Log Out) · the time and workspace dots in the centre ·
  hover drawer (tray, CPU, memory) · network speed · Bluetooth · Wi‑Fi · battery · clipboard ·
  Control Center · date. It never shows which app, page or video is focused.
- **Light & Dark mode** with **eight Apple accent colours** — `Super` `Shift` `T`, the Control
  Center tile, Settings → Appearance or `nothing-theme`. The menu bar, Control Center, widgets,
  notifications, launcher, dock, Settings, kitty, GTK / libadwaita and KDE / Qt apps, lock screen
  and wallpaper all switch live.
- **Ten desktop widgets**, small or medium — Weather, Clock / World Clock, Calendar & agenda,
  System rings, Storage, Batteries, Now Playing, Notes, Network, Focus Timer. Drag them anywhere,
  click them, right-click for size / options / remove, or *Edit Widgets* for remove badges and the
  **Add Widget** gallery.
- **Control Center** — Wi‑Fi · Bluetooth · Microphone, Focus, Night Shift, Dark Mode, sound,
  live CPU graph, memory, CPU/GPU/SSD temperatures, notification history, power buttons with a
  confirm step.
- **Dynamic island** — hover the workspace dots for clock, weather + forecast, calendar, MPRIS
  media (art, progress, controls) and volume; an equaliser while music plays, a red dot while
  recording. Hidden in fullscreen.
- **Notification banners** — top-right squircles under the menu bar: app icon, bold title, round
  buttons, sliding in.
- **Launcher** (`Super` `D`) — Spotlight meets Hyprland: glass inside a two-colour gradient
  frame, big search, an Apps · Run · Windows segmented control, gradient selection.
  **Session menu** (`Super` `Shift` `X`) — the screen frosts over: a lock-screen clock and a
  floating Dock-style bar with a turning gradient border; tiles magnify, risky actions count down.
- **Dock** (nwg-dock) and **night mode** with a schedule (hyprsunset).

**Windows & apps**

- **Traffic lights** — red / yellow / green on the left in GTK and libadwaita header bars; kitty,
  Dolphin and every other window get macOS title bars with the optional
  [hyprbars](https://github.com/hyprwm/hyprland-plugins) plugin.
- **Hairline borders, 14 px continuous corners, deep soft shadows, frosted vibrant blur** — media
  and fullscreen windows stay opaque.
- **Files like Finder** — `Super` `E` opens Nautilus with a translucent sidebar when installed,
  otherwise Dolphin with macOS colour schemes, your accent, SF Pro, double-click to open.
- **SF Pro everywhere** — `scripts/install-sf-fonts.sh` unpacks Apple's `SF-Pro.dmg` /
  `SF-Mono.dmg`; without them fontconfig falls back to Inter / JetBrains Mono.

**System**

- **Settings app** (`Super` `I`) — Network, Bluetooth, Sound, Displays, Appearance (mode, accent,
  border, fonts, text and terminal size, wallpapers with add / delete, opacity, corners, blur),
  Night mode, Notifications, Keyboard & mouse, Power & lock, Login screen, Keyboard shortcuts
  (click one, press the new keys), About. Every option is also a command:
  `nothing-settings set appearance.rounding 12`, `nothing-settings set keys.terminal "SUPER + T"`.
- **One lock screen** — hyprlock only: date above a large SF Pro Rounded clock, blur, battery /
  AC readout, keyboard-layout chip. Optionally boots straight into it (greetd, Hyprland started
  already locked).
- **Security & privacy** — owner-only sockets and data files, no secrets on command lines,
  validated configs and inputs, nothing private on the lock screen or in the bar,
  password-manager copies kept out of clipboard history. See
  [the Guide](docs/GUIDE.md#security--privacy).
- **Any machine** — every screen at its preferred mode; monitors, main screen and devices go in
  one git-ignored file, `~/.config/hypr/hyprland.local.lua` (examples in `hypr/examples/`).
  **Laptops**: battery, low-battery warnings, brightness keys, touchpad gestures, power key →
  session menu, auto-rotation on convertibles.
- **Austrian German, no dead keys** everywhere: Hyprland, hyprlock, login screen, TTY.

## Install

```bash
git clone https://github.com/doveyQ/dotfiles ~/dotfiles
cd ~/dotfiles
make dry-run            # optional: preview every action
make install            # packages, keyboard/services, fonts, symlinks — asks before installing
```

Optional extras for the full macOS look:

```bash
yay -S whitesur-icon-theme          # macOS icons (picked up automatically)
yay -S hyprland-plugin-hyprbars     # title bars + traffic lights for kitty, Dolphin, …
sudo pacman -S nautilus             # Finder-style Files (Super+E prefers it)
```

`hyprland-plugin-hyprbars` is built for one Hyprland version — update both together. Apple's fonts
come from [developer.apple.com/fonts](https://developer.apple.com/fonts/): put `SF-Pro.dmg`
(and `SF-Mono.dmg`) in `~/Downloads`, then `sudo pacman -S 7zip && scripts/install-sf-fonts.sh`.

The installer is idempotent — `make update` pulls and relinks.

| `make …` | |
|---|---|
| `install` | full install (`./install.sh`) |
| `links` | only relink configs, no sudo |
| `dry-run` | preview, change nothing |
| `check` | shellcheck · ruff · JSON(C) · `Hyprland --verify-config` (also run by CI) |
| `selftest` | open every Settings page and fire every control against recorders (changes nothing) |
| `reload` | restart menu bar, shell, notifications, dock, wallpaper, idle daemon |
| `update` | `git pull --ff-only` + relink |

| Flag | Effect |
|---|---|
| `--links-only` | only (re)link configs, no sudo |
| `--no-packages` / `--no-system` / `--no-fonts` | skip a stage |
| `--copy` | copy files instead of symlinking |
| `--dry-run` | print every action without changing anything |
| `-y` | don't ask before installing packages |
| `--no-boot-lock` | keep your distribution's login screen (default: ask, then boot into the lock screen) |
| `--restore-login` | go back to the previous login screen |

What it does:

1. **Packages** — `packages/pacman.txt` via `pacman --needed`, plus `packages/aur.txt` via `yay`
   (bootstrapped if missing).
2. **System** — keymap `at` / `nodeadkeys` (`localectl`, TTY `de-latin1-nodeadkeys`); enables
   `bluetooth` and `NetworkManager`; warns about other lockers so hyprlock is the only one.
3. **Fonts** — unpacks `~/Downloads/SF-*.dmg` into `~/.local/share/fonts/SF-Pro` when present.
4. **Configs** — existing `~/.config/<dir>` folders move to `~/.config-backup/<timestamp>/`, then
   get symlinked to this repo. Helper commands go to `~/.local/bin`, launcher entries to
   `~/.local/share/applications`, the KDE colour schemes to `~/.local/share/color-schemes`. The
   theme is generated (`nothing-theme apply`) and private data is made owner-only.
5. **Verify** — `Hyprland --verify-config`, Python and shell syntax checks; reloads the session if
   Hyprland is running.

Then log out and choose **Hyprland** on the login screen.

## Layout

```
dotfiles/
├── install.sh           idempotent installer (see --help)
├── Makefile             install · links · check · selftest · reload · update
├── docs/GUIDE.md        the full manual
├── scripts/             check.sh (make check, CI) · install-sf-fonts.sh
├── packages/            pacman.txt · aur.txt · laptop.txt (added when a battery is present)
├── settings/            Settings app + nothing-settings CLI (Python/GTK3)
├── system/              login-screen helper + greetd template, laptop logind drop-in
├── hypr/                → ~/.config/hypr
│   ├── hyprland.lua     loader (Hyprland ≥ 0.56 uses Lua, not hyprland.conf)
│   ├── conf/            monitors · autostart · input · look · rules · titlebars · keybinds
│   ├── themes/          mac-dark/ · mac-light/ (palette.css · palette.rasi · theme.lua ·
│   │                    hyprlock.conf · kitty.conf · wallpaper) · typography.css · fonts.conf ·
│   │                    gtk3.css · gtk4.css (traffic lights, Finder sidebar)
│   ├── theme/           generated by nothing-theme (mode + accent) — git-ignored
│   ├── hyprlock.conf    lock screen  ·  hypridle.conf  idle → lock → screens off → suspend
│   ├── examples/        machine files to copy to hyprland.local.lua (desktop, laptop)
│   ├── wallpapers/      mac-dark · mac-light (+ hyprpaper.conf)
│   └── scripts/         nothing-theme · nothing-files · record · battery · brightness · reload …
├── nothing-shell/       → ~/.config/nothing-shell  (island, Control Center, desktop widgets)
├── waybar/              → ~/.config/waybar   (the menu bar, scripts/)
├── swaync/              → ~/.config/swaync   (notification banners)
├── rofi/                → ~/.config/rofi     (launcher, system menu, session menu, pickers)
├── kitty/               → ~/.config/kitty
├── nwg-dock-hyprland/   → ~/.config/nwg-dock-hyprland
├── fontconfig/          → ~/.config/fontconfig  (SF font fallbacks + your interface font)
├── kde/color-schemes/   → ~/.local/share/color-schemes  (macOS Dark / Light for Dolphin & Qt)
├── applications/        → ~/.local/share/applications  (Settings, Power Menu)
└── .github/             CI workflow · issue & PR templates
```

## Keybindings

The defaults — change any of them in **Settings → Keyboard shortcuts** (click, press the new keys);
`Super` `F1` always shows the keys that are active.

| Keys | Action |
|---|---|
| `Super` `Return` | Terminal (kitty) |
| `Super` `D` / `Super` `R` | App launcher |
| `Super` `E` | Files (Nautilus or Dolphin) |
| `Super` `I` | Settings |
| `Super` `N` | Control Center |
| `Super` `A` | Pin the dynamic island open |
| `Super` `Shift` `T` | Light ↔ Dark mode |
| `Super` `Shift` `X` | Session menu — `P` shut down · `R` restart · `S` sleep · `L` lock · `E` log out · `Esc` |
| `Super` `L` | Lock |
| `Super` `Ctrl` `N` | Night mode on / off |
| `Super` `Shift` `N` | Do Not Disturb |
| `Super` `Q` | Close window |
| `Super` `Space` | Toggle floating |
| `Super` `F` | Fullscreen |
| `Super` `S` · `Super` `Alt` `S` | Scratchpad: show / hide · move window there (*minimise* sends windows there too) |
| `Super` `V` | Clipboard history |
| `Super` `←↑→↓` | Focus (up/down crosses monitors) |
| `Super` `Shift` `←↑→↓` | Move window |
| `Super` `Ctrl` `←↑→↓` | Resize window |
| `Alt` `Tab` / `Super` `Tab` | Cycle windows / previous workspace |
| `Super` `1`–`0` · `Super` `Shift` `1`–`0` | Workspace · move window there |
| `Super` `Shift` `S` (or `Print`) | Screenshot of a region → clipboard |
| `Shift` `Print` · `Super` `Shift` `Print` | Screenshot of the screen → ~/Pictures · record the screen |
| `Super` `Shift` `R` | Reload the desktop |
| 3‑finger swipe | Previous / next workspace (touchpad and touchscreen) |
| Brightness keys · Power key | Brightness (with popup) · session menu — laptop |
| `Super` `F1` | Cheat‑sheet |

## Customising

- **Appearance** — Settings → Appearance, or the terminal:
  `nothing-theme toggle|light|dark` · `nothing-theme accent blue|purple|pink|red|orange|yellow|green|graphite`
  · `nothing-theme border hairline|accent|graphite|none`.
- **Your machine** (monitors, main screen, touchpad, …): copy an example —
  `cp ~/.config/hypr/examples/laptop.lua ~/.config/hypr/hyprland.local.lua` — and edit it.
  It's git-ignored, so every computer keeps its own and `git pull` never conflicts.
  Bar on one screen only: `waybar/local.example.jsonc` → `~/.config/waybar/local.jsonc`.
- **Widgets** — `nothing-shell widgets list | types | add TYPE [small|medium] | remove ID|TYPE |
  edit | done | reset`; the layout is `~/.config/nothing/widgets.json`. Agenda: put exported
  `.ics` calendars in `~/.local/share/nothing/calendars/`.
- **Weather location**: `NOTHING_WEATHER_LOCATION=Vienna` — default is IP‑based.
- **Colours**: `hypr/themes/mac-dark/` and `mac-light/` define the same names; `palette.css` feeds
  every GTK surface, `palette.rasi` rofi, `theme.lua` Hyprland, `hyprlock.conf` the lock screen,
  `kitty.conf` the terminal. **Fonts**: `hypr/themes/typography.css`.
- **Window look** (border, rounding, shadows, blur, vibrancy, opacity): `hypr/conf/look.lua`.

## Notes & troubleshooting

Short version below — the full table is in [the Guide §9](docs/GUIDE.md#9-troubleshooting).

- **Hyprland 0.56 dispatch syntax** — `hyprctl dispatch exit` no longer works; use Lua:
  `hyprctl dispatch 'hl.dsp.exit()'`, `hyprctl dispatch 'hl.dsp.dpms({ action = "off" })'`.
- **Hyprland came back in safe mode** (your config is ignored after a crash) — fix the cause, then
  log out and in (`hyprctl dispatch 'hl.dsp.exit()'`). If a plugin is to blame:
  `sudo pacman -R hyprland-plugin-hyprbars` — the title-bar module does nothing without it.
- **Locking** always goes `loginctl lock-session` → hypridle → hyprlock, so there is exactly one
  lock path.
- **"Lockscreen app died" screen**: switch to a TTY (`Ctrl+Alt+F3`), log in and run
  `hyprctl --instance 0 eval 'hl.clear_crashed_lockscreen()'`, then go back.
- **Bluetooth toggle does nothing** — the service is off: `sudo systemctl enable --now bluetooth`.
- **Logs**: `nothing-shell` prints to stderr; run it in a terminal (`nothing-shell quit; nothing-shell`).

## Contributing

PRs welcome — run `make check` (and `make selftest` for Settings changes), follow
[Conventional Commits](https://www.conventionalcommits.org/), see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Apple's SF fonts and the WhiteSur icons are not included and keep their own
licenses.

## Authors

- **[doveyQ](https://github.com/doveyQ)** — author and maintainer
- **Claude** (Anthropic) — co-author: the macOS redesign, desktop widgets, theme system,
  Settings app features and the security pass were written together in
  [Claude Code](https://claude.com/claude-code); those commits carry a
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` trailer.

## Credits

Hyprland, the hypr* ecosystem and [hyprland-plugins](https://github.com/hyprwm/hyprland-plugins) ·
Waybar · SwayNC · Rofi · kitty · nwg-dock · Inter by Rasmus Andersson · JetBrains Mono ·
[WhiteSur](https://github.com/vinceliuice/WhiteSur-icon-theme) and Papirus icons · weather from
[wttr.in](https://wttr.in).
