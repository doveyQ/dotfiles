#!/usr/bin/env bash
# The Apple menu (click the  in the menu bar): About · Settings · Force Quit · Sleep ·
# Restart · Shut Down · Lock · Log Out — like macOS.
theme=~/.config/rofi/applemenu.rasi
bin=~/.local/bin
pidof rofi >/dev/null && { pkill -x rofi; exit 0; }

sep=$'──────────────────────\0nonselectable\x1ftrue'
choice=$(printf '%s\n' "About This Computer" "System Settings…" "$sep" "Force Quit Window" "$sep" \
  "Sleep" "Restart…" "Shut Down…" "$sep" "Lock Screen" "Log Out…" |
  rofi -dmenu -i -no-custom -format s -theme "$theme" -p "")

confirm() {   # confirm <question> — macOS asks before restart / shut down / log out
  [[ $(printf 'Cancel\n%s\n' "$1" | rofi -dmenu -no-custom -theme "$theme" -theme-str 'window { width: 220px; }' -p "") == "$1" ]]
}

case "$choice" in
  "About This Computer") "$bin/nothing-settings" about ;;
  "System Settings…")    "$bin/nothing-settings" ;;
  "Force Quit Window")
    pid=$(hyprctl activewindow -j | python3 -c 'import json,sys; print(json.load(sys.stdin).get("pid", ""))')
    [[ $pid =~ ^[0-9]+$ ]] && kill -9 "$pid" ;;
  "Sleep")       loginctl lock-session; sleep 0.6; systemctl suspend ;;
  "Restart…")    confirm "Restart Now" && systemctl reboot ;;
  "Shut Down…")  confirm "Shut Down Now" && systemctl poweroff ;;
  "Lock Screen") loginctl lock-session ;;
  "Log Out…")    confirm "Log Out Now" && hyprctl dispatch 'hl.dsp.exit()' ;;
esac
