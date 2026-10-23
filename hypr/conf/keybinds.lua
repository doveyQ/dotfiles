-- Programs and key bindings.  `Super`+`F1` shows them (rofi/scripts/keybinds.sh).
return function(ctx)
    local bin, scripts, ui = ctx.bin, ctx.scripts, ctx.ui

    ---------------------
    ---- MY PROGRAMS ----
    ---------------------
    local terminal    = "kitty"
    local fileManager = bin .. "/nothing-files"   -- Nautilus (Finder-style) if installed, else Dolphin
    local browser     = "firefox"
    local launcher    = "rofi -show drun -theme ~/.config/rofi/nothing.rasi"

    local mod = "SUPER"
    local function exec(cmd) return hl.dsp.exec_cmd(cmd) end

    -- Editable shortcuts: Settings → Keyboard shortcuts (or `nothing-settings set keys.<id> "SUPER + T"`).
    -- Your changes live in ~/.config/nothing/settings.lua (ui.binds); "" turns a shortcut off.
    -- One entry per line, `id = …, key = …, desc = …` first — the Settings app reads this block.
    -- shortcuts:begin
    local shortcuts = {
        -- group: Apps & menus
        { id = "terminal",       key = "SUPER + Return",        desc = "Terminal",                     run = exec(terminal) },
        { id = "launcher",       key = "SUPER + D",             desc = "App launcher",                 run = exec(launcher) },
        { id = "launcher_alt",   key = "SUPER + R",             desc = "App launcher (second key)",    run = exec(launcher) },
        { id = "files",          key = "SUPER + E",             desc = "Files",                        run = exec(fileManager) },
        { id = "browser",        key = "SUPER + B",             desc = "Browser",                      run = exec(browser) },
        { id = "settings",       key = "SUPER + I",             desc = "Settings",                     run = exec(bin .. "/nothing-settings") },
        { id = "power_menu",     key = "SUPER + SHIFT + X",     desc = "Session menu",                 run = exec(bin .. "/nothing-power") },
        { id = "control_center", key = "SUPER + N",             desc = "Control Center",               run = exec(bin .. "/nothing-shell control toggle") },
        { id = "island",         key = "SUPER + A",             desc = "Pin the dynamic island open",  run = exec(bin .. "/nothing-shell island toggle") },
        { id = "dnd",            key = "SUPER + SHIFT + N",     desc = "Do Not Disturb on / off",      run = exec(bin .. "/nothing-settings dnd") },
        { id = "night",          key = "SUPER + CTRL + N",      desc = "Night mode on / off",          run = exec(bin .. "/nothing-night toggle") },
        { id = "theme",          key = "SUPER + SHIFT + T",     desc = "Light ↔ Dark mode",            run = exec(bin .. "/nothing-theme toggle") },
        { id = "clipboard",      key = "SUPER + V",             desc = "Clipboard history",            run = exec("cliphist list | rofi -dmenu -theme ~/.config/rofi/nothing.rasi | cliphist decode | wl-copy") },
        { id = "cheatsheet",     key = "SUPER + F1",            desc = "Shortcut cheat-sheet",         run = exec(bin .. "/nothing-keybinds") },
        { id = "lock",           key = "SUPER + L",             desc = "Lock",                         run = exec("loginctl lock-session") },   -- → hypridle → hyprlock
        { id = "reload",         key = "SUPER + SHIFT + R",     desc = "Reload the desktop",           run = exec(scripts .. "/nothing-reload.sh") },
        -- group: Windows
        { id = "close",          key = "SUPER + Q",             desc = "Close window",                 run = hl.dsp.window.close() },
        { id = "float",          key = "SUPER + Space",         desc = "Floating on / off",            run = hl.dsp.window.float({ action = "toggle" }) },
        { id = "fullscreen",     key = "SUPER + F",             desc = "Fullscreen",                   run = hl.dsp.window.fullscreen() },
        { id = "pseudo",         key = "SUPER + P",             desc = "Pseudotile",                   run = hl.dsp.window.pseudo() },
        { id = "split",          key = "SUPER + J",             desc = "Toggle split direction",       run = hl.dsp.layout("togglesplit") },
        { id = "center",         key = "SUPER + C",             desc = "Center window",                run = hl.dsp.window.center() },
        { id = "cycle",          key = "ALT + Tab",             desc = "Cycle windows",                run = hl.dsp.window.cycle_next() },
        { id = "previous_ws",    key = "SUPER + Tab",           desc = "Previous workspace",           run = hl.dsp.focus({ workspace = "previous" }) },
        { id = "scratchpad",     key = "SUPER + S",             desc = "Show / hide the scratchpad",   run = hl.dsp.workspace.toggle_special("magic") },
        { id = "to_scratchpad",  key = "SUPER + ALT + S",       desc = "Move window to the scratchpad", run = hl.dsp.window.move({ workspace = "special:magic" }) },
        -- group: Screenshots & recording
        { id = "shot_region",    key = "SUPER + SHIFT + S",     desc = "Screenshot of a region → clipboard", run = exec(scripts .. "/screenshot.sh region") },
        { id = "shot_region_alt", key = "Print",                desc = "Screenshot of a region (second key)", run = exec(scripts .. "/screenshot.sh region") },
        { id = "shot_full",      key = "SHIFT + Print",         desc = "Screenshot of the screen → ~/Pictures", run = exec(scripts .. "/screenshot.sh full") },
        { id = "record",         key = "SUPER + SHIFT + Print", desc = "Record the screen (start / stop)", run = exec(scripts .. "/record.sh toggle") },
    }
    -- shortcuts:end

    local custom = ui.binds or {}
    for _, s in ipairs(shortcuts) do
        local key = custom[s.id] or s.key
        if key ~= "" then hl.bind(key, s.run, { description = s.id }) end
    end

    -- Recording a new shortcut in Settings: this empty submap lets every key through to the app.
    -- Settings leaves it again by itself; SUPER + Escape is the way out if anything goes wrong.
    hl.define_submap("nothing-capture", function()
        hl.bind("SUPER + Escape", hl.dsp.submap("reset"))
    end)

    -- fixed: arrows, workspace numbers, mouse (listed in the cheat-sheet, not editable)
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
    hl.bind(mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
    hl.bind(mod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))
    hl.bind(mod .. " + mouse:272",  hl.dsp.window.drag(),   { mouse = true })
    hl.bind(mod .. " + mouse:273",  hl.dsp.window.resize(), { mouse = true })

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
