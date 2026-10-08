#!/usr/bin/env bash
# Start hypridle with the timings chosen in Settings → Power & lock (generated), or the
# repo default. Used by hyprland.lua, nothing-reload.sh and nothing-settings.
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/nothing/hypridle.conf"
[ -f "$cfg" ] || cfg="$HOME/.config/hypr/hypridle.conf"
exec hypridle -c "$cfg"
