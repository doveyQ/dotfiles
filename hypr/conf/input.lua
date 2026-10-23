-- Keyboard, pointer, touchpad and gestures.
return function(_)
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
end
