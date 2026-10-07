#!/usr/bin/env bash
# "TITLE · ARTIST" for hyprlock; empty unless something is playing.
[ "$(playerctl status 2>/dev/null)" = Playing ] || exit 0
title=$(playerctl metadata title 2>/dev/null); artist=$(playerctl metadata artist 2>/dev/null)
out="󰎈  ${title:-Unknown}${artist:+  ·  $artist}"
printf '%s\n' "${out:0:64}" | sed 's/&/\&amp;/g; s/</\&lt;/g'
