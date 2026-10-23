#!/usr/bin/env bash
# Open the file manager (Super+E, the Storage widget): Finder-style Nautilus when it's installed
# (translucent sidebar + traffic lights from hypr/themes/gtk4.css), Dolphin otherwise.
# Pin one:  echo dolphin > ~/.config/nothing/files-app   (or nautilus)
pick=$(sed -n '1{/^\(dolphin\|nautilus\)$/p}' "${XDG_CONFIG_HOME:-$HOME/.config}/nothing/files-app" 2>/dev/null)
if [[ -z $pick ]]; then
  if command -v nautilus >/dev/null; then pick=nautilus; else pick=dolphin; fi
fi
case $pick in
  nautilus) exec nautilus --new-window "$@" ;;
  *)        exec dolphin "$@" ;;
esac
