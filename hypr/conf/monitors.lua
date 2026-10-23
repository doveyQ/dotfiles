-- Monitors and workspace placement.  Per output: Settings app first, then the machine
-- file (hyprland.local.lua), then "preferred / auto".
return function(ctx)
    local machine, ui = ctx.machine, ctx.ui

    ------------------
    ---- MONITORS ----
    ------------------
    local seen = {}
    for _, m in ipairs(ui.monitors or {}) do hl.monitor(m); seen[m.output] = true end
    for _, m in ipairs(machine.monitors or {}) do
        if not seen[m.output] then hl.monitor(m) end
    end
    hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

    --------------------
    ---- WORKSPACES ----
    --------------------
    -- workspaces 1-10 always exist; which monitor holds them comes from the machine file
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
end
