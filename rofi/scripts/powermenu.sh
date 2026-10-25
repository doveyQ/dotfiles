#!/usr/bin/env bash
# Session menu (Super+Shift+X): a centred card listing the five actions.
# Single-key accelerators: p r s l e · Enter chooses · Esc cancels.
theme=~/.config/rofi/powermenu.rasi
pidof rofi >/dev/null && { pkill -x rofi; exit 0; }

row() {   # row <glyph> <label> <key>
  printf "<span font_family='Symbols Nerd Font'>%s</span>    %s    <span size='small' alpha='50%%'>%s</span>" "$1" "$2" "$3"
}

entries=(
  "$(row 󰐥 'Shut Down' 'P')"
  "$(row 󰜉 'Restart' 'R')"
  "$(row 󰤄 'Sleep' 'S')"
  "$(row 󰌾 'Lock' 'L')"
  "$(row 󰍃 'Log Out' 'E')"
)
who="$(id -un) · $(uptime -p 2>/dev/null | sed 's/^up //')"

choice=$(printf '%s\n' "${entries[@]}" | rofi -dmenu -markup-rows -format i \
  -no-custom -theme "$theme" -selected-row 3 -u 0 -theme-str "textbox-sub { content: \"$who\"; }" \
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
