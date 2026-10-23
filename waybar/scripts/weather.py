#!/usr/bin/env python3
"""Weather for waybar via wttr.in (cached 15 min).

usage: weather.py [bar|cond|temp|hilo]
Set NOTHING_WEATHER_LOCATION (e.g. "Vienna") to pin a city; default is IP-based.
"""
import json, os, sys, time, urllib.request, urllib.parse

CACHE = os.path.expanduser("~/.cache/nothing-weather.json")
LOC = os.environ.get("NOTHING_WEATHER_LOCATION", "")

# wttr weather codes -> Nerd Font (md-weather) glyphs
ICONS = {
    "113": "󰖙", "116": "󰖕", "119": "󰖐", "122": "󰖐", "143": "󰖑", "248": "󰖑", "260": "󰖑",
    "176": "󰖗", "263": "󰖗", "266": "󰖗", "293": "󰖗", "296": "󰖗", "353": "󰖗",
    "299": "󰖖", "302": "󰖖", "305": "󰖖", "308": "󰖖", "356": "󰖖", "359": "󰖖",
    "179": "󰖘", "182": "󰙿", "185": "󰙿", "227": "󰼶", "230": "󰼶", "323": "󰖘", "326": "󰖘",
    "329": "󰼶", "332": "󰼶", "335": "󰼶", "338": "󰼶", "368": "󰖘", "371": "󰼶",
    "200": "󰙾", "386": "󰙾", "389": "󰙾", "392": "󰙾", "395": "󰙾",
}


def fetch():
    try:
        if time.time() - os.path.getmtime(CACHE) < 900:
            with open(CACHE) as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    try:
        url = f"https://wttr.in/{urllib.parse.quote(LOC)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.load(r)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        fd = os.open(CACHE + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)  # location: owner only
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(CACHE + ".tmp", CACHE)
        return data
    except Exception:
        try:
            with open(CACHE) as f:
                return json.load(f)
        except Exception:
            return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "bar"
    d = fetch()
    if not d:
        print(json.dumps({"text": "󰖑 --" if mode == "bar" else "--", "class": "offline"}, ensure_ascii=False))
        return
    cur = d["current_condition"][0]
    day = d["weather"][0]
    icon = ICONS.get(cur["weatherCode"], "󰖐")
    temp = f'{cur["temp_C"]}°'
    cond = cur["weatherDesc"][0]["value"].strip()
    area = d.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", "")
    tip = f"{area}\n{cond} · feels {cur['FeelsLikeC']}°\nH {day['maxtempC']}°  L {day['mintempC']}°\nhumidity {cur['humidity']}%"
    out = {
        "bar":  f"{icon}  {temp}",
        "cond": f"<span font_family='Symbols Nerd Font' size='28pt'>{icon}</span>   {cond}",
        "temp": temp,
        "hilo": f"↑ {day['maxtempC']}°\n↓ {day['mintempC']}°",
    }[mode]
    print(json.dumps({"text": out, "tooltip": tip, "class": mode}, ensure_ascii=False))


main()
