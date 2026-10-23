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

    -- media, games and screen sharing stay fully opaque despite the 0.96 / 0.90 window opacity
    hl.window_rule({
        name   = "opaque-media",
        match  = { class = "^(mpv|vlc|org.gnome.Loupe|imv|steam_app_.*|gamescope|obs|com.obsproject.Studio)$" },
        opaque = true,
    })
    hl.window_rule({
        name   = "opaque-pip",
        match  = { title = "^(Picture-in-Picture|Bild-im-Bild)$" },
        opaque = true,
    })
    hl.window_rule({
        name   = "opaque-fullscreen",
        match  = { fullscreen = true },
        opaque = true,
    })

    -- frosted glass behind every shell surface (GTK can't blur — Hyprland does). ignore_alpha
    -- keeps the blur off fully transparent pixels (rounded corners, gaps between widgets).
    for _, ns in ipairs({ "waybar", "nothing-island", "nothing-control", "nothing-widgets",
                          "swaync-notification-window", "swaync-control-center", "rofi",
                          "nwg-dock", "gtk-layer-shell", "notifications" }) do
        hl.layer_rule({
            name         = "glass-" .. ns,
            match        = { namespace = "^" .. ns .. "$" },
            blur         = true,
            ignore_alpha = 0.2,
        })
    end
    hl.layer_rule({ name = "control-slide", match = { namespace = "^nothing-control$" }, animation = "slide right" })
    hl.layer_rule({ name = "rofi-fade",     match = { namespace = "^rofi$" },            animation = "fade" })
    -- notification banners slide in from the right edge, like macOS
    hl.layer_rule({ name = "notif-slide",   match = { namespace = "^swaync-notification-window$" }, animation = "slide right" })
    -- the island animates itself; a compositor slide would fight its morph
    hl.layer_rule({ name = "island-static", match = { namespace = "^nothing-island$" },   no_anim = true })
end
