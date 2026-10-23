-- ╺┳┓┏━┓╺┳╸   ┏┓╻┏━┓╺┳╸╻ ╻╻┏┓╻┏━╸
--  ┃┃┃ ┃ ┃    ┃┗┫┃ ┃ ┃ ┣━┫┃┃┗┫┃╺┓   Nothing OS / dot-matrix monochrome
-- ╺┻┛┗━┛ ╹    ╹ ╹┗━┛ ╹ ╹ ╹╹╹ ╹┗━┛   Hyprland 0.56+ (Lua config)
--
-- Hyprland ≥ 0.56 reads hyprland.lua (the old hyprland.conf syntax is gone).
-- Note: on 0.56 `hyprctl dispatch <name> <args>` no longer works — dispatchers are
-- Lua expressions:  hyprctl dispatch 'hl.dsp.exit()'
-- Wiki: https://wiki.hypr.land/Configuring/Start/

------------------
---- PALETTE -----
------------------
local c = {
    black   = "rgba(000000ff)",
    border  = "rgba(333333ff)",
    white   = "rgba(ffffffee)",
    red     = "rgba(d71921ff)",
}

---------------------
---- MY PROGRAMS ----
---------------------
local terminal    = "kitty"
local fileManager = "dolphin"
local browser     = "firefox"
local launcher    = "rofi -show drun -theme ~/.config/rofi/nothing.rasi"
local hypr        = os.getenv("HOME") .. "/.config/hypr"
local bin         = os.getenv("HOME") .. "/.local/bin"
local scripts     = hypr .. "/scripts"

-----------------
---- MACHINE ----
-----------------
-- Everything specific to one computer lives in ~/.config/hypr/hyprland.local.lua
-- (git-ignored — start from hypr/examples/). It returns a table, every field optional:
--   main       output for the island, bar, dock, popups, recorder (→ $NOTHING_OUTPUT)
--   monitors   list of hl.monitor() specs
--   workspace  function(i) → output for workspace i
--   setup      function, runs at the very end: devices, binds, autostart, overrides …
-- Without it: every screen at its preferred mode, workspaces wherever they are opened.
local machine = {}
local localfile = hypr .. "/hyprland.local.lua"
local f = io.open(localfile)
if f then
    f:close()
    machine = dofile(localfile) or {}   -- no pcall: mistakes show up in the error bar
end

-------------------
---- SETTINGS -----
-------------------
-- Choices made in the Settings app (Super+I) or `nothing-settings set …` are generated into
-- ~/.config/nothing/settings.lua (outside the repo). They win over the machine file.
local ui = {}
local uifile = os.getenv("HOME") .. "/.config/nothing/settings.lua"
local uf = io.open(uifile)
if uf then
    uf:close()
    ui = dofile(uifile) or {}
end
if ui.main then machine.main = ui.main end

------------------
---- MONITORS ----
------------------
-- per output: Settings app first, then the machine file, then "preferred / auto"
local seen = {}
for _, m in ipairs(ui.monitors or {}) do hl.monitor(m); seen[m.output] = true end
for _, m in ipairs(machine.monitors or {}) do
    if not seen[m.output] then hl.monitor(m) end
end
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

-- Login managers don't read ~/.bashrc, so the session PATH lacks ~/.local/bin (where
-- install.sh puts nothing-*). Add it before anything is launched.
local path = os.getenv("PATH") or "/usr/local/bin:/usr/bin:/bin"
if not (":" .. path .. ":"):find(":" .. bin .. ":", 1, true) then   -- reloads re-run this file
    hl.env("PATH", bin .. ":" .. path)
end

-------------------
---- AUTOSTART ----
-------------------
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE PATH")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd(scripts .. "/wallpaper.sh")                    -- hyprpaper (Settings → Appearance)
    hl.exec_cmd(scripts .. "/idle.sh")                        -- hypridle: the ONLY idle/lock manager → hyprlock
    hl.exec_cmd("hyprsunset -i")                              -- night mode backend (nothing-night drives it)
    hl.exec_cmd("swaync")                                     -- notification popups
    hl.exec_cmd(bin .. "/nothing-shell")                      -- dynamic island + control center
    hl.exec_cmd("waybar")                                     -- logo + status pill
    hl.exec_cmd("waybar -c ~/.config/waybar/desktop.jsonc -s ~/.config/waybar/desktop.css") -- desktop widgets
    hl.exec_cmd("nwg-dock-hyprland -d -i 36 -mb 10 " .. (machine.main and ("-o " .. machine.main) or "") .. " -s nothing.css")
    hl.exec_cmd("wl-paste --watch cliphist store")
    hl.exec_cmd(scripts .. "/battery-warn.sh")                -- low-battery popups (exits without a battery)
end)

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
hl.env("LIBVA_DRIVER_NAME", "radeonsi")   -- AMD / Mesa VA-API
if machine.main then hl.env("NOTHING_OUTPUT", machine.main) end   -- island, dock, recorder, reload script

-----------------------
---- LOOK AND FEEL ----
-----------------------
hl.config({
    general = {
        gaps_in     = 8,
        gaps_out    = 12,
        border_size = 1,
        col = {
            active_border   = { colors = { "rgba(ffffffee)", "rgba(bbbbbbaa)" }, angle = 45 },
            inactive_border = c.border,
        },
        resize_on_border = true,
        allow_tearing    = false,
        layout           = "dwindle",
    },

    decoration = {
        rounding       = 18,
        rounding_power = 2.5,   -- squircle-ish, like Nothing's cards
        active_opacity   = 1.0,
        inactive_opacity = 0.94,
        dim_special      = 0.4,

        shadow = {
            enabled      = true,
            range        = 18,
            render_power = 3,
            color        = 0x99000000,
        },

        -- subtle red glow around the focused window
        glow = {
            enabled        = true,
            range          = 10,
            render_power   = 3,
            color          = "rgba(d7192155)",
            color_inactive = "rgba(00000000)",
        },

        blur = {
            enabled           = true,
            size              = 6,
            passes            = 3,
            noise             = 0.02,
            contrast          = 1.0,
            brightness        = 0.8,
            vibrancy          = 0.0,  -- keep it monochrome
            popups            = true,
            new_optimizations = true,
        },
    },

    animations = { enabled = true },
})

hl.curve("nothing", { type = "bezier", points = { {0.2, 0.9}, {0.1, 1} } })
hl.curve("linear",  { type = "bezier", points = { {0, 0}, {1, 1} } })
hl.curve("snappy",  { type = "spring", mass = 1, stiffness = 260, dampening = 26 })

hl.animation({ leaf = "global",     enabled = true, speed = 8,   bezier = "default" })
hl.animation({ leaf = "border",     enabled = true, speed = 5,   bezier = "nothing" })
hl.animation({ leaf = "windows",    enabled = true, speed = 4.5, spring = "snappy" })
hl.animation({ leaf = "windowsIn",  enabled = true, speed = 4,   spring = "snappy", style = "popin 90%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.5, bezier = "linear", style = "popin 90%" })
hl.animation({ leaf = "fade",       enabled = true, speed = 3,   bezier = "nothing" })
hl.animation({ leaf = "layersIn",   enabled = true, speed = 3.5, bezier = "nothing", style = "slide top" })
hl.animation({ leaf = "layersOut",  enabled = true, speed = 1.5, bezier = "linear",  style = "fade" })
hl.animation({ leaf = "fadeLayersIn",  enabled = true, speed = 2.5, bezier = "nothing" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.8, bezier = "linear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3,   bezier = "nothing", style = "slidevert" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3, bezier = "nothing", style = "slidevert" })

hl.config({
    dwindle = { preserve_split = true },
    master  = { new_status = "master" },
    misc = {
        force_default_wallpaper  = 0,
        disable_hyprland_logo    = true,
        disable_splash_rendering = true,
        background_color         = c.black,
        vrr                      = 2,
        focus_on_activate        = true,
        key_press_enables_dpms   = true,
        mouse_move_enables_dpms  = true,
        allow_session_lock_restore = true,  -- if hyprlock ever crashes, a new one can take over
    },
    binds = {
        workspace_back_and_forth = false,
        allow_workspace_cycles   = true,
    },
    cursor = {
        default_monitor = machine.main,   -- nil → Hyprland's default
    },
    render = {
        direct_scanout = 2, -- games only, safe on AMD
    },
    ecosystem = {
        no_update_news  = true,
        no_donation_nag = true,
    },
})

---------------
---- INPUT ----
---------------
-- Austrian German, no dead keys (^ ´ ` type immediately).  The same layout is set
-- system-wide via `localectl` (login screen / TTY) by install.sh, and hyprlock
-- inherits it from Hyprland.
hl.config({
    input = {
        kb_layout          = "at",
        kb_variant         = "nodeadkeys",
        kb_model           = "pc105",
        numlock_by_default = true,
        follow_mouse       = 1,
        sensitivity        = 0,
        accel_profile      = "flat",
        touchpad = {
            natural_scroll       = false,  -- set true in hyprland.local.lua if you like it
            tap_to_click         = true,
            disable_while_typing = true,
            clickfinger_behavior = true,   -- 2-finger click = right, 3-finger = middle
        },
    },
    gestures = {
        workspace_swipe_distance = 300,
        workspace_swipe_create_new = false,
    },
})

-- 3-finger swipe → previous / next workspace
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

--------------------
---- WORKSPACES ----
--------------------
-- workspaces 1-10 always exist; which monitor holds them comes from MACHINE (optional)
local ws_monitor = machine.workspace or function() return nil end
for i = 1, 10 do
    local mon = ws_monitor(i)
    hl.workspace_rule({
        workspace  = tostring(i),
        monitor    = mon,
        default    = mon ~= nil and (i == 1 or mon ~= ws_monitor(i - 1)),   -- first one per monitor
        persistent = true,
    })
end

---------------------
---- KEYBINDINGS ----
---------------------
local mod = "SUPER"
local function exec(cmd) return hl.dsp.exec_cmd(cmd) end

-- apps & menus
hl.bind(mod .. " + Return",       exec(terminal))
hl.bind(mod .. " + D",            exec(launcher))
hl.bind(mod .. " + R",            exec(launcher))
hl.bind(mod .. " + E",            exec(fileManager))
hl.bind(mod .. " + B",            exec(browser))
hl.bind(mod .. " + I",            exec(bin .. "/nothing-settings"))
hl.bind(mod .. " + SHIFT + X",    exec(bin .. "/nothing-power"))
hl.bind(mod .. " + N",            exec(bin .. "/nothing-shell control toggle"))
hl.bind(mod .. " + A",            exec(bin .. "/nothing-shell island toggle"))
hl.bind(mod .. " + SHIFT + N",    exec(bin .. "/nothing-settings dnd"))
hl.bind(mod .. " + CTRL + N",     exec(bin .. "/nothing-night toggle"))
hl.bind(mod .. " + V",            exec("cliphist list | rofi -dmenu -theme ~/.config/rofi/nothing.rasi | cliphist decode | wl-copy"))
hl.bind(mod .. " + F1",           exec(bin .. "/nothing-keybinds"))
hl.bind(mod .. " + L",            exec("loginctl lock-session"))   -- → hypridle → hyprlock
hl.bind(mod .. " + SHIFT + R",    exec(scripts .. "/nothing-reload.sh"))

-- windows
hl.bind(mod .. " + Q",            hl.dsp.window.close())
hl.bind(mod .. " + Space",        hl.dsp.window.float({ action = "toggle" }))
hl.bind(mod .. " + F",            hl.dsp.window.fullscreen())
hl.bind(mod .. " + P",            hl.dsp.window.pseudo())
hl.bind(mod .. " + J",            hl.dsp.layout("togglesplit"))
hl.bind(mod .. " + C",            hl.dsp.window.center())
hl.bind("ALT + Tab",              hl.dsp.window.cycle_next())
hl.bind(mod .. " + Tab",          hl.dsp.focus({ workspace = "previous" }))

for _, d in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(mod .. " + " .. d,          hl.dsp.focus({ direction = d }))        -- up/down also crosses monitors
    hl.bind(mod .. " + SHIFT + " .. d,  hl.dsp.window.move({ direction = d }))
end
hl.bind(mod .. " + CTRL + left",  hl.dsp.window.resize({ x = -40, y = 0,   relative = true }), { repeating = true })
hl.bind(mod .. " + CTRL + right", hl.dsp.window.resize({ x = 40,  y = 0,   relative = true }), { repeating = true })
hl.bind(mod .. " + CTRL + up",    hl.dsp.window.resize({ x = 0,   y = -40, relative = true }), { repeating = true })
hl.bind(mod .. " + CTRL + down",  hl.dsp.window.resize({ x = 0,   y = 40,  relative = true }), { repeating = true })

-- workspaces (rules above route them to the right monitor)
for i = 1, 10 do
    local key = i % 10
    hl.bind(mod .. " + " .. key,         hl.dsp.focus({ workspace = i }))
    hl.bind(mod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end
hl.bind(mod .. " + S",          hl.dsp.workspace.toggle_special("magic"))
hl.bind(mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))
hl.bind(mod .. " + mouse:272",  hl.dsp.window.drag(),   { mouse = true })
hl.bind(mod .. " + mouse:273",  hl.dsp.window.resize(), { mouse = true })

-- screenshots / recording (red dot appears in the island while recording)
hl.bind(mod .. " + SHIFT + S",     exec("grim -g \"$(slurp)\" - | wl-copy && notify-send -a Screenshot 'Region copied'"))
hl.bind("SHIFT + Print",           exec("grim ~/Pictures/$(date +%F_%H-%M-%S).png && notify-send -a Screenshot 'Saved to ~/Pictures'"))
hl.bind(mod .. " + SHIFT + Print", exec(scripts .. "/record.sh toggle"))

-- media keys (work on the lock screen too)
hl.bind("XF86AudioRaiseVolume", exec("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", exec("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true })
hl.bind("XF86AudioMute",        exec("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true })
hl.bind("XF86AudioMicMute",     exec("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { locked = true })
hl.bind("XF86AudioNext",  exec("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", exec("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  exec("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  exec("playerctl previous"),   { locked = true })

-- laptop keys (no-ops on the desktop keyboard)
hl.bind("XF86MonBrightnessUp",   exec(scripts .. "/brightness.sh up"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", exec(scripts .. "/brightness.sh down"), { locked = true, repeating = true })
hl.bind("XF86PowerOff",          exec(bin .. "/nothing-power"))   -- logind ignores the key (install.sh), so no instant power-off

--------------------------------
---- WINDOW & LAYER RULES ------
--------------------------------
hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

hl.window_rule({
    name   = "float-settings-tools",
    match  = { class = "^(org.pulseaudio.pavucontrol|pavucontrol|blueman-manager|nm-connection-editor|nwg-look|nothing-float|com.saivert.pwvucontrol)$" },
    float  = true,
    size   = "860 600",
    center = true,
})

hl.window_rule({
    name   = "nothing-settings",
    match  = { class = "^(dev.nothing.Settings|nothing-settings)$" },
    float  = true,
    size   = "1040 720",
    center = true,
})

-- frosted glass for every Nothing surface
for _, ns in ipairs({ "waybar", "nothing-island", "nothing-control", "swaync-notification-window", "rofi", "nwg-dock" }) do
    hl.layer_rule({
        name         = "glass-" .. ns,
        match        = { namespace = "^" .. ns .. "$" },
        blur         = true,
        ignore_alpha = 0.3,
    })
end
hl.layer_rule({ name = "control-slide", match = { namespace = "^nothing-control$" }, animation = "slide right" })
hl.layer_rule({ name = "rofi-fade",     match = { namespace = "^rofi$" },            animation = "fade" })
-- the island animates itself; a compositor slide would fight its morph
hl.layer_rule({ name = "island-static", match = { namespace = "^nothing-island$" },   no_anim = true })

--------------------------------
---- MACHINE-LOCAL OVERRIDES ---
--------------------------------
-- hyprland.local.lua's setup() runs last, so it can override anything above (see MACHINE)
if machine.setup then machine.setup() end

-- Settings app choices (keyboard, mouse, touchpad, gaps, blur …) are applied last
if ui.config then hl.config(ui.config) end
