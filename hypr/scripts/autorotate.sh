#!/usr/bin/env bash
# Auto-rotation for convertibles — only while folded into tablet mode.
#   autorotate.sh daemon <output>   follow the accelerometer (started from hyprland.local.lua)
#   autorotate.sh tablet on|off     from the tablet-mode switch binds
# Needs iio-sensor-proxy (monitor-sensor). Rotates the screen, touchscreen and pen together.
# state lives in the per-user runtime dir (never /tmp: its contents end up in `hyprctl eval`)
state=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/nothing-rotate
mkdir -p "$state" && chmod 700 "$state" && [[ -O $state ]] || exit 1

apply() {   # apply <orientation>
  local out t
  out=$(<"$state/output") || return
  [[ $out =~ ^[A-Za-z0-9_.-]{1,32}$ ]] || return   # a connector name, nothing that could be Lua
  case "$1" in
    normal) t=0 ;; left-up) t=1 ;; bottom-up) t=2 ;; right-up) t=3 ;; *) return ;;
  esac
  hyprctl eval "hl.monitor({ output = '$out', mode = 'preferred', position = '0x0', scale = 1, transform = $t })" >/dev/null
  hyprctl eval "hl.config({ input = { touchdevice = { transform = $t }, tablet = { transform = $t } } })" >/dev/null
}

case "$1" in
  daemon)
    echo "${2:-eDP-1}" >"$state/output"
    pkill -f "monitor-sensor --accel" 2>/dev/null
    stdbuf -oL monitor-sensor --accel | while read -r line; do
      case "$line" in
        *"orientation changed: "*) o=${line##*changed: } ;;
        *"(orientation: "*)        o=${line##*orientation: }; o=${o%%,*} ;;
        *) continue ;;
      esac
      echo "$o" >"$state/orientation"
      [ -e "$state/tablet" ] && apply "$o"
    done ;;
  tablet)
    if [ "$2" = on ]; then
      touch "$state/tablet"
      apply "$(cat "$state/orientation" 2>/dev/null || echo normal)"
    else
      rm -f "$state/tablet"
      apply normal
    fi ;;
  *) sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
