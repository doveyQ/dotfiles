#!/usr/bin/env bash
# Battery readout for hyprlock (dot bar + %). Desktops without a battery show "AC".
for b in /sys/class/power_supply/BAT*; do
  [ -r "$b/capacity" ] || continue
  cap=$(<"$b/capacity"); st=$(<"$b/status")
  n=$(( (cap + 5) / 10 )); bar=""
  for ((i = 0; i < 10; i++)); do (( i < n )) && bar+="●" || bar+="○"; done
  icon="󰁹"; [ "$st" = Charging ] && icon="󰂄"; (( cap <= 15 )) && [ "$st" != Charging ] && icon="<span foreground='##d71921'>󰂃</span>"
  echo "$icon  $bar  $cap%"
  exit 0
done
echo "󰚥  AC POWER"
