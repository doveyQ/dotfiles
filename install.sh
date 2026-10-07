#!/usr/bin/env bash
# ┏┓╻┏━┓╺┳╸╻ ╻╻┏┓╻┏━╸  dotfiles installer — Nothing OS dot-matrix Hyprland desktop
# ┃┗┫┃ ┃ ┃ ┣━┫┃┃┗┫┃╺┓  Idempotent: safe to run again after `git pull`.
# ╹ ╹┗━┛ ╹ ╹ ╹╹╹ ╹┗━┛
#
#   ./install.sh                 everything (packages, system settings, fonts, links)
#   ./install.sh --links-only    only (re)link configs — no sudo needed
#   ./install.sh --copy          copy files instead of symlinking
#   ./install.sh --dry-run       print what would happen
#   ./install.sh -y              don't ask before installing packages
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
FONTS="$HOME/.local/share/fonts/nothing"
BACKUP="$HOME/.config-backup/$(date +%Y%m%d-%H%M%S)"
FONT_REPO="https://github.com/xeji01/nothingfont"

# config dirs in the repo → ~/.config/<name>
CONFIG_DIRS=(hypr waybar swaync rofi kitty nwg-dock-hyprland nothing-shell)
# executables → ~/.local/bin/<name>
declare -A BINS=(
  [nothing-shell]="nothing-shell/nothing-shell.py"
  [nothing-settings]="rofi/scripts/settings.sh"
  [nothing-power]="rofi/scripts/powermenu.sh"
  [nothing-keybinds]="rofi/scripts/keybinds.sh"
  [nothing-reload]="hypr/scripts/nothing-reload.sh"
)

DO_PACKAGES=1 DO_SYSTEM=1 DO_FONTS=1 MODE=link DRY=0 YES=0

for arg in "$@"; do
  case "$arg" in
    --links-only) DO_PACKAGES=0; DO_SYSTEM=0; DO_FONTS=0 ;;
    --no-packages) DO_PACKAGES=0 ;;
    --no-system)  DO_SYSTEM=0 ;;
    --no-fonts)   DO_FONTS=0 ;;
    --copy)       MODE=copy ;;
    --dry-run)    DRY=1 ;;
    -y|--yes)     YES=1 ;;
    -h|--help)    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (see --help)"; exit 1 ;;
  esac
done

# ── output helpers ─────────────────────────────────────────
R=$'\e[38;2;215;25;33m' W=$'\e[1;97m' D=$'\e[2m' N=$'\e[0m'
step() { printf '\n%s●%s %s%s%s\n' "$R" "$N" "$W" "$*" "$N"; }
info() { printf '  %s·%s %s\n' "$D" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$R" "$N" "$*"; }
run()  { if ((DRY)); then printf '  %s$ %s%s\n' "$D" "$*" "$N"; else "$@"; fi; }

[[ $EUID -eq 0 ]] && { echo "Run as your normal user (sudo is used where needed)."; exit 1; }
command -v pacman >/dev/null || { echo "This installer targets Arch / EndeavourOS (pacman)."; exit 1; }

printf '%s\n' "${W}nothing dotfiles${N}  ${D}${REPO}${N}"

read_list() { grep -vE '^\s*(#|$)' "$1" | awk '{print $1}'; }

# ── 1. packages ─────────────────────────────────────────
if ((DO_PACKAGES)); then
  step "Packages"
  mapfile -t pkgs < <(read_list "$REPO/packages/pacman.txt")
  mapfile -t missing < <(pacman -T "${pkgs[@]}" || true)
  if ((${#missing[@]})); then
    info "missing: ${missing[*]}"
    flags=(--needed); ((YES)) && flags+=(--noconfirm)
    run sudo pacman -S "${flags[@]}" "${missing[@]}"
  else
    info "all ${#pkgs[@]} repo packages present"
  fi

  mapfile -t aur < <(read_list "$REPO/packages/aur.txt")
  if ((${#aur[@]})); then
    if ! command -v yay >/dev/null; then
      info "bootstrapping yay"
      tmp=$(mktemp -d)
      run sudo pacman -S --needed --noconfirm base-devel git
      run git clone --depth 1 https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
      ((DRY)) || (cd "$tmp/yay-bin" && makepkg -si --noconfirm)
      rm -rf "$tmp"
    fi
    flags=(--needed); ((YES)) && flags+=(--noconfirm)
    run yay -S "${flags[@]}" "${aur[@]}"
  fi
fi

# ── 2. system settings (keyboard, services, lockers) ─────────────────────────
if ((DO_SYSTEM)); then
  step "System"
  # Austrian German, no dead keys — login screen (SDDM / plasmalogin read this) + TTY
  if [[ "$(localectl status | awk -F': ' '/X11 Layout/{print $2}')" != "at" ]] ||
     [[ "$(localectl status | awk -F': ' '/X11 Variant/{print $2}')" != "nodeadkeys" ]]; then
    run sudo localectl set-x11-keymap at pc105 nodeadkeys
  else
    info "X11 keymap already at / nodeadkeys"
  fi
  if [[ "$(localectl status | awk -F': ' '/VC Keymap/{print $2}')" != "de-latin1-nodeadkeys" ]]; then
    run sudo localectl set-keymap --no-convert de-latin1-nodeadkeys
  else
    info "TTY keymap already de-latin1-nodeadkeys"
  fi

  # services the widgets talk to
  for svc in bluetooth NetworkManager; do
    if systemctl list-unit-files "$svc.service" >/dev/null 2>&1 && ! systemctl is-enabled -q "$svc" 2>/dev/null; then
      run sudo systemctl enable --now "$svc"
    else
      info "$svc.service enabled"
    fi
  done

  # one lock screen only: hyprlock (via hypridle). Other lockers would fight over the session lock.
  for p in swaylock swaylock-effects swayidle xss-lock gtklock; do
    if pacman -Q "$p" >/dev/null 2>&1; then
      warn "$p is installed — remove it so only hyprlock locks:  sudo pacman -Rns $p"
    fi
  done
  info "hyprlock is the only locker (hypridle → loginctl lock-session → hyprlock)"
fi

# ── 3. fonts ─────────────────────────────────────────
if ((DO_FONTS)); then
  step "Fonts"
  if fc-list : family | grep -x "Ndot 57" >/dev/null; then   # (no -q: SIGPIPE + pipefail)
    info "Nothing dot-matrix fonts already installed"
  else
    tmp=$(mktemp -d)
    run git clone --quiet --depth 1 "$FONT_REPO" "$tmp/nothingfont"
    run mkdir -p "$FONTS"
    ((DRY)) || find "$tmp/nothingfont" -type f \( -iname '*.otf' -o -iname '*.ttf' \) -exec cp {} "$FONTS/" \;
    rm -rf "$tmp"
    run fc-cache -f "$FONTS"
    info "installed Ndot 55/57, NType 82, Space Mono → $FONTS"
  fi
fi

# ── 4. link configs ─────────────────────────────────────────
step "Configs ($MODE)"

backup() {          # move a real file/dir out of the way (never touches our own symlinks)
  local target=$1
  run mkdir -p "$BACKUP"
  run mv "$target" "$BACKUP/"
  info "backed up $(basename "$target") → $BACKUP/"
}

place() {           # place <repo-path> <target>
  local src=$1 dst=$2
  if [[ -L "$dst" && "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then
    info "ok      ${dst/#$HOME/\~}"
    return
  fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ -L "$dst" ]]; then run rm "$dst"; else backup "$dst"; fi
  fi
  run mkdir -p "$(dirname "$dst")"
  if [[ $MODE == copy ]]; then run cp -r "$src" "$dst"; else run ln -s "$src" "$dst"; fi
  info "linked  ${dst/#$HOME/\~}"
}

for d in "${CONFIG_DIRS[@]}"; do place "$REPO/$d" "$CONFIG/$d"; done
for name in "${!BINS[@]}"; do
  run chmod +x "$REPO/${BINS[$name]}"
  place "$REPO/${BINS[$name]}" "$BIN/$name"
done
for f in "$REPO"/applications/*.desktop; do place "$f" "$APPS/$(basename "$f")"; done
run chmod +x "$REPO"/hypr/scripts/*.sh "$REPO"/waybar/scripts/*.sh "$REPO"/waybar/scripts/*.py "$REPO"/rofi/scripts/*.sh
command -v update-desktop-database >/dev/null && run update-desktop-database -q "$APPS" || true

# ── 5. verify ─────────────────────────────────────────
step "Verify"
if command -v Hyprland >/dev/null; then
  if Hyprland --verify-config -c "$CONFIG/hypr/hyprland.lua" 2>&1 | grep "config ok" >/dev/null; then
    info "hyprland.lua: config ok"
  else
    warn "hyprland.lua has errors:"; Hyprland --verify-config -c "$CONFIG/hypr/hyprland.lua" 2>&1 | sed -n '/parsing result/,$p'
  fi
fi
python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$REPO/nothing-shell/nothing-shell.py" && info "nothing-shell: parses"
for s in "$REPO"/hypr/scripts/*.sh "$REPO"/rofi/scripts/*.sh "$REPO"/waybar/scripts/*.sh; do
  bash -n "$s" || warn "syntax error in $s"
done
info "scripts: syntax ok"
case ":$PATH:" in *":$BIN:"*) ;; *) warn "$BIN is not on PATH — add it to your shell profile" ;; esac

# ── 6. apply ─────────────────────────────────────────
if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && ((!DRY)); then
  step "Reloading the running Hyprland session"
  "$REPO/hypr/scripts/nothing-reload.sh" >/dev/null 2>&1 || true
  info "done"
else
  step "Done"
  info "Log out and pick ‘Hyprland’ at the login screen."
fi
((DRY)) && info "(dry run — nothing was changed)"
exit 0
