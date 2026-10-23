-- Session environment and autostart.
return function(ctx)
    local machine, bin, scripts = ctx.machine, ctx.bin, ctx.scripts

    -- Login managers don't read ~/.bashrc, so the session PATH lacks ~/.local/bin (where
    -- install.sh puts nothing-*). Add it before anything is launched.
    local path = os.getenv("PATH") or "/usr/local/bin:/usr/bin:/bin"
    if not (":" .. path .. ":"):find(":" .. bin .. ":", 1, true) then   -- reloads re-run this file
        hl.env("PATH", bin .. ":" .. path)
    end

    -------------------------------
    ---- ENVIRONMENT VARIABLES ----
    -------------------------------
    hl.env("XCURSOR_SIZE", "24")
    hl.env("HYPRCURSOR_SIZE", "24")
    hl.env("QT_QPA_PLATFORM", "wayland;xcb")
    hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
    hl.env("QT_QPA_PLATFORMTHEME", "kde")    -- Qt apps (Dolphin) follow kdeglobals: macOS colours, SF Pro, icons
    hl.env("MOZ_ENABLE_WAYLAND", "1")
    hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
    hl.env("LIBVA_DRIVER_NAME", "radeonsi")   -- AMD / Mesa VA-API
    if machine.main then hl.env("NOTHING_OUTPUT", machine.main) end   -- island, dock, recorder, reload script

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
        hl.exec_cmd(bin .. "/nothing-shell")                      -- island, Control Center, desktop widgets
        hl.exec_cmd("waybar")                                     -- the menu bar
        hl.exec_cmd("nwg-dock-hyprland -d -i 36 -mb 10 " .. (machine.main and ("-o " .. machine.main) or "") .. " -s nothing.css")
        -- clipboard history: capped; entries that password managers mark as secret
        -- (x-kde-passwordManagerHint → CLIPBOARD_STATE=sensitive) are never stored
        hl.exec_cmd("wl-paste --watch cliphist -max-items 200 store")
        hl.exec_cmd(scripts .. "/battery-warn.sh")                -- low-battery popups (exits without a battery)
    end)
end
