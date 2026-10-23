#!/usr/bin/env bash
# Light / Dark mode.  Installed as `nothing-theme`; Super+Shift+T, the Control Center tile
# and Settings → Appearance call it. Also themes KDE / Qt apps (Dolphin) like Finder.
#
#   nothing-theme [toggle|dark|light|status]
#
# The active theme is the git-ignored link ~/.config/hypr/theme → themes/mac-dark|mac-light.
# Everything reads its colours through that link; this script repoints it and reloads
# each piece in place (no restart of the session).
set -uo pipefail

HYPR="${XDG_CONFIG_HOME:-$HOME/.config}/hypr"
LINK="$HYPR/theme"
current=$(basename "$(readlink "$LINK" 2>/dev/null || echo mac-dark)")
current=${current#mac-}

case "${1:-toggle}" in
  status) echo "$current"; exit 0 ;;
  dark|light) mode=$1 ;;
  toggle) [[ $current == dark ]] && mode=light || mode=dark ;;
  *) echo "usage: nothing-theme [toggle|dark|light|status]" >&2; exit 1 ;;
esac

ln -sfn "themes/mac-$mode" "$LINK"

# GTK / libadwaita / portal apps follow the system appearance
if command -v gsettings >/dev/null; then
  gsettings set org.gnome.desktop.interface color-scheme "prefer-$mode" 2>/dev/null
  gtk=$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null | tr -d "'")
  case "$gtk" in
    Breeze|Breeze-Dark)   gsettings set org.gnome.desktop.interface gtk-theme "$([[ $mode == dark ]] && echo Breeze-Dark || echo Breeze)" ;;
    Adwaita|Adwaita-dark) gsettings set org.gnome.desktop.interface gtk-theme "$([[ $mode == dark ]] && echo Adwaita-dark || echo Adwaita)" ;;
  esac
fi

# KDE / Qt apps — Dolphin as Finder: colour scheme (kde/color-schemes), Papirus icons (blue
# folders), SF Pro, double-click to open, no menu bar, small sidebar icons. Running KDE apps
# are told to re-read colours and icons.
apply_kde() {
  command -v kwriteconfig6 >/dev/null || return 0
  local scheme=MacDark icons=Papirus-Dark accent="#0A84FF" k=kwriteconfig6
  [[ $mode == light ]] && { scheme=MacLight; icons=Papirus-Light; accent="#007AFF"; }
  local ui="SF Pro Text,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
  $k --file kdeglobals --group General --key font "$ui"
  $k --file kdeglobals --group General --key menuFont "$ui"
  $k --file kdeglobals --group General --key toolBarFont "$ui"
  $k --file kdeglobals --group General --key smallestReadableFont "SF Pro Text,8,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
  $k --file kdeglobals --group General --key fixed "SF Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
  $k --file kdeglobals --group KDE --key widgetStyle Breeze
  $k --file kdeglobals --group KDE --key SingleClick false
  $k --file kdeglobals --group Icons --key Theme "$icons"
  $k --file dolphinrc --group MainWindow --key MenuBar Disabled
  $k --file dolphinrc --group General --key ShowZoomSlider false
  $k --file dolphinrc --group General --key ShowSelectionToggle false
  $k --file dolphinrc --group PlacesPanel --key IconSize 16
  # scheme first, then an explicit accent on top: with --accent-color the tool applies only
  # the accent, and without one a previous scheme's accent (selection, focus, links) is kept
  if command -v plasma-apply-colorscheme >/dev/null; then
    plasma-apply-colorscheme "$scheme" >/dev/null 2>&1
    plasma-apply-colorscheme --accent-color "$accent" >/dev/null 2>&1
  fi
  # tell running KDE apps: palette changed (the accent pass alone isn't announced), icons changed
  if command -v dbus-send >/dev/null; then
    dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange \
      int32:0 int32:0 >/dev/null 2>&1
    dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 >/dev/null 2>&1
  fi
  return 0
}
apply_kde

[[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] || { echo "$mode (applies at next login)"; exit 0; }

hyprctl reload >/dev/null                                   # borders, shadows, blur (theme.lua)
pkill -USR2 -x waybar                                       # menu bar: reload style
command -v swaync-client >/dev/null && swaync-client -rs >/dev/null 2>&1
"$HOME/.local/bin/nothing-shell" reload-css >/dev/null 2>&1 # island, Control Center, widgets
pkill -USR1 -x kitty                                        # terminals re-read kitty.conf

# the dock reads its CSS only at start
if pgrep -f nwg-dock-hyprland >/dev/null; then
  pkill -f nwg-dock-hyprland
  (nwg-dock-hyprland -d -i 36 -mb 10 ${NOTHING_OUTPUT:+-o "$NOTHING_OUTPUT"} -s nothing.css >/dev/null 2>&1 &)
fi

# wallpaper follows the mode unless one was picked in Settings → Appearance
if [[ ! -f "${XDG_CONFIG_HOME:-$HOME/.config}/nothing/hyprpaper.conf" ]]; then
  pkill -x hyprpaper
  ("$HYPR/scripts/wallpaper.sh" >/dev/null 2>&1 &)
fi

echo "$mode"
