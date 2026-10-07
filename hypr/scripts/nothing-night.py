#!/usr/bin/env python3
"""nothing-night — night mode (warm screen) with an optional schedule, via hyprsunset.

  nothing-night                      toggle
  nothing-night on | off | toggle    manual switch (overrides the schedule until its next change)
  nothing-night temp <K>             warmth when on, 1000–6500 (default 4000)
  nothing-night schedule HH:MM HH:MM turn on at the first time, off at the second
  nothing-night schedule off         disable the schedule
  nothing-night status [--json]
  nothing-night tick                 apply the schedule (run every minute by nothing-shell)
  nothing-night apply                re-apply the current state (e.g. after login)
  nothing-night menu                 rofi menu (Settings hub → Night Mode)

State lives in ~/.local/state/nothing/night.json (machine-local, not in git).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")), "nothing")
STATE = os.path.join(STATE_DIR, "night.json")
DEFAULTS = {"on": False, "temp": 4000, "applied": 6500,
            "schedule": {"enabled": False, "start": "20:00", "end": "07:00"}, "phase": None}
DAY_K = 6500
THEME = os.path.expanduser("~/.config/rofi/settings.rasi")


# ── state ─────────────────────────────────────────
def load():
    try:
        with open(STATE) as f:
            s = json.load(f)
    except (OSError, ValueError):
        s = {}
    out = {**DEFAULTS, **s}
    out["schedule"] = {**DEFAULTS["schedule"], **s.get("schedule", {})}
    return out


def save(s):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f, indent=2)
    os.replace(tmp, STATE)


def notify_shell():
    """Let the island / control center redraw (no-op if nothing-shell isn't running)."""
    subprocess.run(["nothing-shell", "night-changed"], capture_output=True, timeout=2)


# ── hyprsunset ─────────────────────────────────────────
def hyprsunset(*args):
    return subprocess.run(["hyprctl", "hyprsunset", *map(str, args)], capture_output=True, text=True, timeout=3)


def ensure_daemon():
    def ready():
        r = hyprsunset("temperature")
        return r.returncode == 0 and r.stdout.strip().isdigit()
    if subprocess.run(["pgrep", "-x", "hyprsunset"], capture_output=True).returncode == 0:
        for _ in range(30):                 # running but maybe still starting up
            if ready():
                return True
            time.sleep(0.1)
        return False
    if not shutil.which("hyprsunset"):
        print("hyprsunset is not installed: sudo pacman -S hyprsunset", file=sys.stderr)
        return False
    subprocess.Popen(["hyprsunset", "-i"], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        time.sleep(0.1)
        if ready():
            return True
    return False


def fade(s, target, ms=900, steps=18):
    """Ease the colour temperature from the last applied value to `target`."""
    if not ensure_daemon():
        return
    start = int(s.get("applied") or DAY_K)
    if start != target:
        for i in range(1, steps + 1):
            t = i / steps
            k = start + (target - start) * (1 - (1 - t) ** 3)   # ease-out cubic
            hyprsunset("temperature", int(k))
            time.sleep(ms / 1000 / steps)
    if target >= DAY_K:
        hyprsunset("identity")          # exact passthrough when off
    else:
        hyprsunset("temperature", target)
    s["applied"] = target


def apply(s, animate=True):
    target = int(s["temp"]) if s["on"] else DAY_K
    if animate:
        fade(s, target)
    elif ensure_daemon():
        hyprsunset("identity") if target >= DAY_K else hyprsunset("temperature", target)
        s["applied"] = target
    save(s)
    notify_shell()


# ── schedule ─────────────────────────────────────────
def minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def scheduled_phase(sched, now=None):
    now = now or time.localtime()
    cur = now.tm_hour * 60 + now.tm_min
    a, b = minutes(sched["start"]), minutes(sched["end"])
    night = (a <= cur < b) if a < b else (cur >= a or cur < b)   # window may cross midnight
    return "night" if night else "day"


def valid_time(t):
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", t.strip())
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def tick(s):
    """Switch only when the schedule's phase changes, so manual toggles stick until then."""
    if not s["schedule"]["enabled"]:
        return
    phase = scheduled_phase(s["schedule"])
    if phase != s.get("phase"):
        s["phase"] = phase
        s["on"] = phase == "night"
        apply(s)
        subprocess.run(["notify-send", "-a", "Night mode", "-u", "low",
                        "Night mode on" if s["on"] else "Night mode off",
                        f"{s['temp']} K until {s['schedule']['end']}" if s["on"]
                        else f"back on at {s['schedule']['start']}"], capture_output=True)


def describe(s):
    sch = s["schedule"]
    return {
        "on": s["on"], "temp": s["temp"],
        "schedule": sch["enabled"], "start": sch["start"], "end": sch["end"],
        "text": ("ON" if s["on"] else "OFF") + (f" · {s['temp']} K" if s["on"] else "")
        + (f" · schedule {sch['start']}–{sch['end']}" if sch["enabled"] else ""),
    }


# ── rofi menu ─────────────────────────────────────────
def rofi(options, prompt="NIGHT MODE", lines=None, custom=False):
    args = ["rofi", "-dmenu", "-i", "-format", "i" if not custom else "s", "-theme", THEME,
            "-theme-str", f'entry {{ placeholder: "{prompt}"; }} listview {{ columns: 1; lines: {lines or len(options)}; }} window {{ width: 520px; }}']
    if not custom:
        args.append("-no-custom")
    r = subprocess.run(args, input="\n".join(options), capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0 or out == "":
        return None
    return out if custom else int(out)


def menu(s):
    sch = s["schedule"]
    items = [
        ("toggle", f"󰖔   Night mode   ·   {'ON — turn off' if s['on'] else 'OFF — turn on'}"),
        ("temp", f"󰔄   Warmth   ·   {s['temp']} K"),
        ("schedule", f"󰥔   Schedule   ·   {sch['start']} → {sch['end']}" if sch["enabled"] else "󰥔   Schedule   ·   off"),
    ]
    i = rofi([t for _, t in items])
    if i is None:
        return
    key = items[i][0]
    if key == "toggle":
        s["on"] = not s["on"]
        apply(s)
    elif key == "temp":
        presets = [(5500, "subtle"), (4500, "warm"), (4000, "warmer — default"), (3500, "very warm"), (2800, "candle")]
        j = rofi([f"{'●' if k == s['temp'] else '○'}   {k} K   ·   {n}" for k, n in presets], "WARMTH")
        if j is not None:
            s["temp"] = presets[j][0]
            if not s["on"]:
                s["on"] = True          # picking a warmth implies you want to see it
            apply(s)
    elif key == "schedule":
        opts = [("off", "○   Off"), (("20:00", "07:00"), "●   Evening   ·   20:00 → 07:00"),
                (("22:00", "06:30"), "●   Late   ·   22:00 → 06:30"), (("19:00", "08:00"), "●   Long   ·   19:00 → 08:00"),
                ("custom", "✎   Custom times…")]
        j = rofi([t for _, t in opts], "SCHEDULE")
        if j is None:
            return
        choice = opts[j][0]
        if choice == "off":
            set_schedule(s, None)
        elif choice == "custom":
            a = valid_time(rofi([], "TURN ON AT  (HH:MM)", lines=0, custom=True) or "")
            b = valid_time(rofi([], "TURN OFF AT  (HH:MM)", lines=0, custom=True) or "") if a else None
            if not (a and b):
                subprocess.run(["notify-send", "-a", "Night mode", "Invalid time", "Use 24-hour HH:MM, e.g. 21:30"])
                return
            set_schedule(s, (a, b))
        else:
            set_schedule(s, choice)


def set_schedule(s, times):
    if times is None:
        s["schedule"]["enabled"] = False
        s["phase"] = None
        save(s)
        notify_shell()
        return
    s["schedule"].update(enabled=True, start=times[0], end=times[1])
    s["phase"] = None               # force the next tick to apply the current phase
    tick(s)


# ── cli ─────────────────────────────────────────
def main(argv):
    s = load()
    cmd = argv[0] if argv else "toggle"
    if cmd in ("on", "off", "toggle"):
        s["on"] = {"on": True, "off": False}.get(cmd, not s["on"])
        apply(s)
    elif cmd == "temp" and len(argv) == 2 and argv[1].isdigit():
        s["temp"] = max(1000, min(6500, int(argv[1])))
        apply(s)
    elif cmd == "schedule" and argv[1:] == ["off"]:
        set_schedule(s, None)
    elif cmd == "schedule" and len(argv) == 3:
        a, b = valid_time(argv[1]), valid_time(argv[2])
        if not (a and b):
            sys.exit("times must be HH:MM (24 h)")
        set_schedule(s, (a, b))
    elif cmd == "status":
        d = describe(s)
        print(json.dumps(d) if "--json" in argv else d["text"])
    elif cmd == "tick":
        tick(s)
    elif cmd == "apply":                   # at login: hyprsunset starts neutral, snap to the right state
        s["applied"] = DAY_K
        if s["schedule"]["enabled"]:
            s["phase"] = scheduled_phase(s["schedule"])
            s["on"] = s["phase"] == "night"
        apply(s, animate=False)
    elif cmd == "menu":
        menu(s)
    else:
        print(__doc__.strip())
        sys.exit(0 if cmd in ("-h", "--help", "help") else 2)


if __name__ == "__main__":
    main(sys.argv[1:])
