#!/usr/bin/env bash
# Session menu.  Single-key accelerators: p r s l e · Esc cancels.
theme=~/.config/rofi/powermenu.rasi
hint=$(sed -n 's/^ *dim: *\(#[0-9a-fA-F]\{6\}\).*/\1/p' ~/.config/hypr/theme/palette.rasi 2>/dev/null); hint=${hint:-#a39c91}
pidof rofi >/dev/null && { pkill -x rofi; exit 0; }

tile() { printf "<span font_family='Symbols Nerd Font' size='26pt'>%s</span>\n\n<span size='12pt' weight='500'>%s</span>  <span size='10pt' foreground='%s'>%s</span>" "$1" "$2" "$hint" "$3"; }

entries=(
  "$(tile 󰐥 'Power off' 'P')"
  "$(tile 󰜉 'Restart' 'R')"
  "$(tile 󰤄 'Sleep' 'S')"
  "$(tile 󰌾 'Lock' 'L')"
  "$(tile 󰍃 'Log out' 'E')"
)

choice=$(printf '%s|' "${entries[@]}" | rofi -dmenu -sep '|' -eh 5 -markup-rows -format i \
  -no-custom -theme "$theme" -selected-row 3 -u 0 \
  -kb-custom-1 p -kb-custom-2 r -kb-custom-3 s -kb-custom-4 l -kb-custom-5 e \
  -kb-cancel "Escape,q")
code=$?

case "$code" in
  10) choice=0 ;; 11) choice=1 ;; 12) choice=2 ;; 13) choice=3 ;; 14) choice=4 ;;
  0) ;;
  *) exit 0 ;;
esac

# NOTHING_DRYRUN=1 prints the action instead of running it (used for testing)
[ -n "$NOTHING_DRYRUN" ] && { echo "action=$choice"; exit 0; }

case "$choice" in
  0) systemctl poweroff ;;
  1) systemctl reboot ;;
  2) loginctl lock-session; sleep 0.6; systemctl suspend ;;
  3) loginctl lock-session ;;
  4) hyprctl dispatch 'hl.dsp.exit()' ;;
esac
