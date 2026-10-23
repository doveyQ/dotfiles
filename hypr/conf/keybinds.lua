-- Programs and key bindings.  `Super`+`F1` shows them (rofi/scripts/keybinds.sh).
return function(ctx)
    local bin, scripts = ctx.bin, ctx.scripts

    ---------------------
    ---- MY PROGRAMS ----
    ---------------------
    local terminal    = "kitty"
    local fileManager = "dolphin"
    local browser     = "firefox"
    local launcher    = "rofi -show drun -theme ~/.config/rofi/nothing.rasi"

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
    hl.bind(mod .. " + SHIFT + T",    exec(bin .. "/nothing-theme toggle"))   -- light ↔ dark
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

    -- workspaces (rules in monitors.lua route them to the right monitor)
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

    -- screenshots / recording (a red dot appears in the bar while recording)
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
end
