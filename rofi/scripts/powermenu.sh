#!/usr/bin/env bash
# Nothing power overlay.  Single-key accelerators: p r s l e · Esc cancels.
theme=~/.config/rofi/powermenu.rasi
pidof rofi >/dev/null && { pkill -x rofi; exit 0; }

tile() { printf "<span font_family='Symbols Nerd Font' size='28pt'>%s</span>\n\n<span font_family='Ndot 55' size='13pt' letter_spacing='1024'>%s</span>  <span font_family='Ndot 57' size='13pt' foreground='#d71921'>%s</span>" "$1" "$2" "$3"; }

entries=(
  "$(tile 󰐥 'POWER' 'P')"
  "$(tile 󰜉 'REBOOT' 'R')"
  "$(tile 󰤄 'SLEEP' 'S')"
  "$(tile 󰌾 'LOCK' 'L')"
  "$(tile 󰍃 'LOG OUT' 'E')"
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
