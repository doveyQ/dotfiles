#!/usr/bin/env bash
# Nothing settings hub (Super+I).  Also: nothing-settings <wifi|bluetooth|audio|displays|...>
term() { kitty --class nothing-float -o initial_window_width=96c -o initial_window_height=28c "$@" & }
edit() { term -e "${EDITOR:-nano}" "$1"; }
cfg=~/.config/hypr

run() {
  case "$1" in
    wifi)       command -v nm-connection-editor >/dev/null && [ "$2" = gui ] && exec nm-connection-editor
                term -e nmtui ;;
    bluetooth)  if ! systemctl is-active -q bluetooth; then
                  notify-send -a Bluetooth "Bluetooth service is off" "Run: sudo systemctl enable --now bluetooth"
                  exit 1
                fi
                exec blueman-manager ;;
    audio)      exec pavucontrol ;;
    displays)   exec nwg-displays ;;
    appearance) exec nwg-look ;;
    keyboard)   notify-send -a Keyboard "Layout: $(hyprctl getoption input:kb_layout | awk '/str/{print $2}') · $(hyprctl getoption input:kb_variant | awk '/str/{print $2}')" "Edit the INPUT section of hyprland.lua"
                edit "$cfg/hyprland.lua" ;;
    wallpaper)  pick=$(find "$cfg/wallpapers" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' \) -printf '%f\n' | sort |
                       rofi -dmenu -theme ~/.config/rofi/nothing.rasi -p "●")
                [ -n "$pick" ] || exit 0
                hyprctl hyprpaper wallpaper ",$cfg/wallpapers/$pick" >/dev/null
                sed -i "s|^\(\s*path = \).*|\1$cfg/wallpapers/$pick|" "$cfg/hyprpaper.conf" ;;
    night)      exec nothing-night menu ;;
    dnd)        swaync-client -d -sw >/dev/null; pkill -RTMIN+9 waybar ;;
    idle)       edit "$cfg/hypridle.conf" ;;
    lock)       edit "$cfg/hyprlock.conf" ;;
    hyprland)   edit "$cfg/hyprland.lua" ;;
    kde)        exec systemsettings ;;
    keys)       exec ~/.config/rofi/scripts/keybinds.sh ;;
    reload)     exec ~/.config/hypr/scripts/nothing-reload.sh ;;
    power)      exec ~/.config/rofi/scripts/powermenu.sh ;;
    *)          return 1 ;;
  esac
}

[ -n "$1" ] && { run "$@"; exit; }

# label · key  (icon glyphs are Nerd Font)
menu="󰤨   Wi-Fi & Network|wifi
󰂯   Bluetooth|bluetooth
󰕾   Sound|audio
󰍹   Displays|displays
󰏘   Appearance|appearance
󰌌   Keyboard|keyboard
󰸉   Wallpaper|wallpaper
󰖔   Night Mode|night
󰂛   Do Not Disturb|dnd
󰒲   Idle & Sleep|idle
󰌾   Lock Screen|lock
󰈙   Hyprland Config|hyprland
󰋖   Keybindings|keys
󰑓   Reload Desktop|reload
󰒓   KDE System Settings|kde"

choice=$(cut -d'|' -f1 <<<"$menu" | rofi -dmenu -i -theme ~/.config/rofi/settings.rasi -format i)
[ -n "$choice" ] || exit 0
run "$(sed -n "$((choice + 1))p" <<<"$menu" | cut -d'|' -f2)"
