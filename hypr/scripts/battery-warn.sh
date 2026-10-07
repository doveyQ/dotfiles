#!/usr/bin/env bash
# Low-battery warnings, started by hyprland.lua (exits right away without a battery).
# One notification per level while discharging: 20 % normal, 10 % critical (stays until
# dismissed). upower still handles the emergency action at its own critical level.
compgen -G "/sys/class/power_supply/BAT*" >/dev/null || exit 0
warned=100
while sleep 60; do
  for b in /sys/class/power_supply/BAT*; do
    [ -r "$b/capacity" ] || continue
    cap=$(<"$b/capacity"); st=$(<"$b/status")
    if [ "$st" != Discharging ]; then warned=100; continue; fi
    if (( cap <= 10 && warned > 10 )); then
      notify-send -a Battery -u critical -h string:x-canonical-private-synchronous:battery "Battery critical — $cap%" "Plug in now"
      warned=10
    elif (( cap <= 20 && warned > 20 )); then
      notify-send -a Battery -u normal -h string:x-canonical-private-synchronous:battery "Battery low — $cap%" "Consider plugging in"
      warned=20
    fi
    break
  done
done
