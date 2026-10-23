#!/usr/bin/env bash
# Reload the whole Nothing desktop inside a running Hyprland (Super+Shift+R).
cfg=~/.config
hyprctl reload >/dev/null
~/.local/bin/nothing-shell quit 2>/dev/null
pkill -x waybar; pkill -x swaync; pkill -x hyprpaper; pkill -f nwg-dock-hyprland
sleep 0.4
~/.config/hypr/scripts/wallpaper.sh >/dev/null 2>&1 &
swaync >/dev/null 2>&1 &
~/.local/bin/nothing-shell >/dev/null 2>&1 &
waybar >/dev/null 2>&1 &
command -v nwg-dock-hyprland >/dev/null && nwg-dock-hyprland -d -i 36 -mb 10 ${NOTHING_OUTPUT:+-o "$NOTHING_OUTPUT"} -s nothing.css >/dev/null 2>&1 &
pkill -x hypridle; sleep 0.2; ~/.config/hypr/scripts/idle.sh >/dev/null 2>&1 &
disown -a
sleep 0.8
notify-send -a Desktop "Desktop reloaded" "Menu bar · Control Center · widgets · wallpaper"
