#!/usr/bin/env bash
# Screen brightness keys with a dot-bar popup (swaync replaces it in place).
#   brightness.sh up|down
case "$1" in
  up)   brightnessctl -q -e4 -n2 set 5%+ ;;
  down) brightnessctl -q -e4 -n2 set 5%- ;;
  *)    echo "usage: brightness.sh up|down"; exit 1 ;;
esac
pct=$(brightnessctl -m | cut -d, -f4 | tr -d %)
notify-send -a Brightness -u low -t 1200 -h string:x-canonical-private-synchronous:brightness \
  -h "int:value:$pct" "Brightness" "$pct%"
