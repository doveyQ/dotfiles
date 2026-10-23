#!/usr/bin/env bash
# Menu-bar date, macOS style: "Fri 23 Oct" (English), month calendar as tooltip.
# (The time sits in the centre of the bar, next to the workspace dots — nothing-shell.)
export LC_TIME=en_US.UTF-8
text=$(date '+%a %-d %b')
cal=$(cal -m --color=never 2>/dev/null | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
python3 -c 'import json,sys; print(json.dumps({"text": sys.argv[1], "tooltip": "<tt>" + sys.argv[2] + "</tt>"}))' "$text" "$cal"
