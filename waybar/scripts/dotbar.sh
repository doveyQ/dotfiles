#!/usr/bin/env bash
# Nothing-style dot progress bars:  dotbar.sh cpu|ram|both [json]
cells=12
bar() { local n=$(( ($1 * cells + 50) / 100 )) s=""; for ((i=0;i<cells;i++)); do (( i < n )) && s+="●" || s+="○"; done; echo "$s"; }
cpu() {
  read -r _ a b c idle rest < /proc/stat; t1=$((a+b+c+idle)); i1=$idle; sleep 0.4
  read -r _ a b c idle rest < /proc/stat; t2=$((a+b+c+idle)); i2=$idle
  echo $(( 100 * ( (t2-t1) - (i2-i1) ) / (t2-t1) ))
}
ram() { awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "%d", (t-a)*100/t}' /proc/meminfo; }
case "$1" in
  cpu) cpu ;;
  ram) ram ;;
  both)
    c=$(cpu); r=$(ram)
    txt="CPU  $(bar $c)  $(printf '%3d' $c)%\nRAM  $(bar $r)  $(printf '%3d' $r)%"
    printf '{"text":"%s","tooltip":"CPU %s%% · RAM %s%%"}\n' "$txt" "$c" "$r" ;;
esac
