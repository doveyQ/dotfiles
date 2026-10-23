#!/usr/bin/env bash
# Screenshots (keys: Settings → Keyboard shortcuts).
#   screenshot.sh region   drag a region → clipboard   (Esc cancels)
#   screenshot.sh full     focused screen → ~/Pictures/<date>.png (+ clipboard)
case "$1" in
  region)
    geo=$(slurp 2>/dev/null) || exit 0          # cancelled
    grim -g "$geo" - | wl-copy --type image/png &&
      notify-send -a Screenshot -h string:x-canonical-private-synchronous:shot "Region copied" "Paste it anywhere with Ctrl+V" ;;
  full)
    dir=$(xdg-user-dir PICTURES 2>/dev/null || echo ~/Pictures); mkdir -p "$dir"
    file="$dir/$(date +%F_%H-%M-%S).png"
    out=$(hyprctl -j monitors | python3 -c 'import json,sys; print(next((m["name"] for m in json.load(sys.stdin) if m["focused"]), ""))')
    grim ${out:+-o "$out"} "$file" && wl-copy --type image/png <"$file" &&
      notify-send -a Screenshot -i "$file" -h string:x-canonical-private-synchronous:shot "Screenshot saved" "${file/#$HOME/\~}" ;;
  *) sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
