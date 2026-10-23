-- Window and layer rules.
return function(_)
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

    -- frosted glass behind every shell surface (GTK can't blur — Hyprland does)
    for _, ns in ipairs({ "waybar", "nothing-island", "nothing-control", "swaync-notification-window", "rofi", "nwg-dock" }) do
        hl.layer_rule({
            name         = "glass-" .. ns,
            match        = { namespace = "^" .. ns .. "$" },
            blur         = true,
            ignore_alpha = 0.25,
        })
    end
    hl.layer_rule({ name = "control-slide", match = { namespace = "^nothing-control$" }, animation = "slide right" })
    hl.layer_rule({ name = "rofi-fade",     match = { namespace = "^rofi$" },            animation = "fade" })
    -- the island animates itself; a compositor slide would fight its morph
    hl.layer_rule({ name = "island-static", match = { namespace = "^nothing-island$" },   no_anim = true })
end
