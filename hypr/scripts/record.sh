#!/usr/bin/env bash
# Screen recording with a red Nothing-style dot in the island.
#   record.sh toggle   start/stop (select region with slurp; Esc = full DP-2)
#   record.sh status   JSON for waybar
#   record.sh state    true/false for swaync toggle
sig() { pkill -RTMIN+8 waybar; }   # waybar status pill shows the red dot
case "$1" in
  toggle)
    if pgrep -x wf-recorder >/dev/null; then
      pkill -INT -x wf-recorder; sig
      notify-send -a Recorder "Recording saved" "$(ls -t ~/Videos/rec-*.mp4 2>/dev/null | head -1)"
    else
      geo=$(slurp 2>/dev/null)
      file=~/Videos/rec-$(date +%F_%H-%M-%S).mp4
      if [ -n "$geo" ]; then wf-recorder -g "$geo" -f "$file" & else wf-recorder -o DP-2 -f "$file" & fi
      sleep 0.3; sig
    fi ;;
  status)
    if pgrep -x wf-recorder >/dev/null; then
      echo '{"text":"●","class":"recording","tooltip":"Recording — click to stop"}'
    else
      echo '{"text":"","class":"idle"}'
    fi ;;
  state) pgrep -x wf-recorder >/dev/null && echo true || echo false ;;
esac
