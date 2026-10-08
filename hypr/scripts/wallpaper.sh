#!/usr/bin/env bash
# Start hyprpaper with the wallpaper chosen in Settings → Appearance (generated), or the
# repo default.
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/nothing/hyprpaper.conf"
[ -f "$cfg" ] || cfg="$HOME/.config/hypr/hyprpaper.conf"
exec hyprpaper -c "$cfg"
