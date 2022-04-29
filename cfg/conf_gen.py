from enum import Enum
import inspect
Δ = dict

class conf_gen(Enum):
    plain = inspect.cleandoc(f'''
        default_orientation auto
        floating_modifier Mod4
        focus_follows_mouse no
        focus_on_window_activation smart
        focus_wrapping workspace
        force_display_urgency_hint 2000 ms
        mouse_warping none
        workspace_layout tabbed
        default_border normal
        default_floating_border normal
        font pango: Iosevka Bold 12
        hide_edge_borders both
        show_marks yes
        title_align left
        '''
    )

    rules = inspect.cleandoc(f'''
        for_window [class=".*"] title_format "<span foreground=\'#395573\'> >_ </span> %title", border pixel 5
        for_window [class="^(Gcolor3|rdesktop|openssh-askpass)$"] floating enable
        for_window [class="^(inkscape|gimp)$"] move workspace $draw
        for_window [class="(?i)(?:steam|lutris)"] floating enable
        for_window [title="(?i)(?:copying|deleting|moving)"] floating enable
        for_window [class="steam_app_.*"] floating enable
        for_window [instance="^(gpartedbin|recoll)$"] move workspace $sys, floating enable, focus
        for_window [title="Firefox — Sharing Indicator"] border pixel 1, sticky enable, move position 20 ppt -5 px
        for_window [title="alsamixer"] floating enable border pixel 1
        for_window [title="File Transfer*"] floating enable
        for_window [title="i3_help"] floating enable sticky enable border normal
        for_window [class="pavucontrol-qt"] floating enable border normal
        for_window [class="qt5ct"] floating enable sticky enable border normal
        no_focus [class="zoom" instance="zoom" title="^zoom$"]
        no_focus [title="Firefox — Sharing Indicator"]
        no_focus [window_type="splash"]
        '''
    )

    startup = Δ(
        always = Δ(
            negwm = 'systemctl --user restart --no-block negwm.service',
        ),
        once = Δ(
            dbus_env = 'dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK',
            startup = 'systemctl --user start --no-block i3-session.target'
        ),
    )

    workspaces = [
        '︁ α:term',
        ' β:web',
        ' δ:dev',
        ' γ:doc',
        ' ζ:draw',
        ' ε:gfx',
        '@ ρ:obs',
        ' ξ:pic',
        ' ι:steam',
        ' η:sys',
        ' λ:vm',
        ' μ:wine'
    ]


    colors = inspect.cleandoc(f'''
        # set_from_resource $background background
        # set_from_resource $foreground foreground
        client.background        #000000ee
        client.focused           #000011dd  #000000ee  #ddddee  #112211  #0C0C0D
        client.focused_inactive  #000000dd  #000000ee  #005fff  #000000  #020204
        client.placeholder       #000000ee  #000000    #ffffff  #000000  #0c0c0c
        client.unfocused         #000000ee  #000000    #315c70  #000000  #020204
        client.urgent            #000000ee  #2E2457    #4C407C  #32275E  #32275E
    '''
    )

    exec = Δ(
        no_startup_id = {
            ('Mod1+grave'): 'rofi -show run -show-icons -disable-history -theme neg',
            ('Mod4+8'): 'playerctl volume 0.0 || amixer -q set Master 0 mute',
            ('Mod4+c'): '~/bin/clip',
            ('Mod4+g'): '~/bin/g',
            ('Mod4+p'): '~/bin/rofi-tmux-urls',
            ('Mod4+m'): '~/bin/music-rename current',
            ('Mod4+Shift+6'): '~/bin/wl',
            ('Mod4+Shift+8'): 'playerctl volume 1.0 || amixer -q set Master 65536 unmute',
            ('Mod4+Shift+9'): 'dunstctl history-pop',
            ('Mod4+Shift+i'): '~/bin/rofi-nm',
            ('Mod4+Shift+l'): '~/bin/rofi-lutris',
            ('Mod4+Shift+m'): '~/bin/rofi-audio',
            ('Mod4+Shift+y'): '~/bin/clip youtube-dw-list',
            ('Mod4+space'): 'dunstctl close-all',
            ('XF86Sleep'): 'sudo systemctl suspend'
        },
        plain = {
            ('Mod4+4'): '~/bin/screenshot',
            ('Mod4+Control+4'): '~/bin/screenshot -r',
            ('Mod4+Shift+4'): 'flameshot gui'
        }
    )

    bindings = Δ(
        default = Δ(
            focus = Δ(
                modkey = 'Mod4',
                keymap = Δ(
                    down = ['j'],
                    left = ['h'],
                    right = ['l'],
                    up = ['k']
                ),
                post = 'focus'
            ),
            i3 = Δ(
                modkey = 'Mod4',
                keymap = Δ(
                    reload = ['apostrophe'],
                    restart = ['Shift+apostrophe']
                ),
            ),
            vol = Δ(
                keymap = Δ(
                    d = ['XF86AudioLowerVolume'],
                    u = ['XF86AudioRaiseVolume']
                ),
                post = '$vol'
            ),
            remember_focused = Δ(
                keymap = Δ(
                    focus_next_visible = ['Mod4+grave'],
                    focus_prev_visible = ['Mod4+Shift+grave'],
                    switch = ['Mod1+Tab', 'Mod4+slash']
                ),
                post = '$remember_focused'
            ),
            scratchpad = Δ(
                modkey = 'Mod4',
                keymap = Δ(
                    dialog = ['Control+a'],
                    geom_dump = ['Control+s'],
                    geom_restore = ['Control+space'],
                    hide_current = ['s'],
                    next = ['3']
                ),
                post = '$scratchpad'
            ),
            media = Δ(
                modkey = 'Mod4',
                keymap = {
                    'next': ['period'],
                    'play-pause': ['Shift+2'],
                    'previous': ['comma']
                },
                post = 'exec --no-startup-id playerctl'
            ),
            media_xf86 = Δ(
                keymap = {
                    'next': ['XF86AudioNext'],
                    'play': ['XF86AudioPlay'],
                    'previous': ['XF86AudioPrev'],
                    'stop': ['XF86AudioStop']
                },
                post = 'exec --no-startup-id playerctl'
            ),
            menu = Δ(
                keymap = Δ(
                    attach = ['Mod4+Shift+a'],
                    autoprop = ['Mod4+Shift+s'],
                    cmd_menu = ['Mod4+Control+grave'],
                    goto_win = ['Mod1+g'],
                    movews = ['Mod4+Control+g'],
                    ws = ['Mod1+Control+g']
                ),
                post = '$menu'
            ),
            misc = Δ(
                modkey = 'Mod4',
                keymap = {
                    'fullscreen toggle': ['q'],
                    'kill': ['Control+q']
                },
            ),
        ),
        resize = Δ(
            bind = 'Mod4+r',
            plus = Δ(
                keymap = Δ(
                    bottom = {"binds": ['j', 's'], "param": '4'},
                    left = {"binds": ['h', 'a'], "param": '4'},
                    right = {"binds": ['l', 'd'], "param": '4'},
                    top = {"binds": ['k', 'w'], "param": '4'},
                ),
                post = '$actions resize'
            ),
            minus = Δ(
                modkey = 'Shift',
                keymap = Δ(
                    bottom = {"binds": ['j', 's'], "param": '-4'},
                    left = {"binds": ['h', 'a'], "param": '-4'},
                    right = {"binds": ['l', 'd'], "param": '-4'},
                    top = {"binds": ['k', 'w'], "param": '-4'},
                ),
                post = '$actions resize'
            )
        ),
        spec = Δ(
            bind = 'Mod1+e',
            misc = Δ(
                keymap = {
                    '[urgent=latest] focus': ['e'],
                    'floating toggle': ['Shift+d'],
                    'exec i3lockr -p 8 ': ['l'],
                }
            ),
            menu = Δ(
                keymap = Δ(
                    gtk_theme = ['Shift+t'],
                    icon_theme = ['Shift+i'],
                    pulse_input = ['i'],
                    pulse_output = ['o'],
                    xprop_show = ['m']
                ),
                post = '$menu'
            ),
        ),
        wm = Δ(
            bind = 'Mod4+minus',
            layout = Δ(
                keymap = Δ(
                   default = ['grave'],
                   splith = ['minus'],
                   splitv = ['backslash'],
                   tabbed = ['t'],
                   toggle = ['Control+t'],
                ),
                post = 'layout',
            ),
            split = Δ(
                keymap = Δ(
                    horizontal = ['h', 'l'],
                    vertical = ['j', 'k']
                ),
                post = 'split',
            ),
            move = Δ(
                keymap = Δ(
                    bottom = ['s'],
                    left = ['a'],
                    right = ['d'],
                    top = ['w']
                ),
                post = 'move'
            ),
            actions = Δ(
                keymap = Δ(
                    grow = ['Shift+plus'],
                    maxhor = ['x'],
                    maximize = ['m'],
                    maxvert = ['y'],
                    none = ['c'],
                    resize = ['Shift+c'],
                    revert_maximize = ['Shift+m', 'Shift+x', 'Shift+y'],
                    shrink = ['Shift+minus'],
                    hdown = {"binds": ['Shift+w'], "param": 'x2'},
                    hup = {"binds": ['Shift+a'], "param": 'x2'},
                    vleft = {"binds": ['Shift+s'], "param": 'x2'},
                    vright = {"binds": ['Shift+d'], "param": 'x2'},
                ),
                post = '$actions'
            )
        )
    )
