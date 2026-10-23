#!/usr/bin/env bash
# Menu-bar clock, macOS style: "Fri 23 Oct  1:07 PM" (English, 12-hour), month calendar as
# tooltip. A script because Waybar's clock module can't drop leading zeros (%-I).
export LC_TIME=en_US.UTF-8
text=$(date '+%a %-d %b   %-I:%M %p')
cal=$(cal -m --color=never 2>/dev/null | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
python3 -c 'import json,sys; print(json.dumps({"text": sys.argv[1], "tooltip": "<tt>" + sys.argv[2] + "</tt>"}))' "$text" "$cal"
