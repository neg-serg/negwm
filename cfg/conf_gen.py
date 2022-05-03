from enum import Enum
import inspect
import sys
sys.path.append("../lib")
from keymap import keymap
from keymap import bindmap
Δ = bindmap
λ = keymap

class conf_gen(Enum):
    M1 = 'Mod1'
    M4 = 'Mod4'
    Sh = 'Shift'
    Ct = 'Control'

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

    exec = (
        'dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK',
        'systemctl --user start --no-block i3-session.target'
    )
    exec_always = ('systemctl --user restart --no-block negwm.service',)

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
        client.background        #000000ee
        client.focused           #000011dd  #000000ee  #ddddee  #112211  #0C0C0D
        client.focused_inactive  #000000dd  #000000ee  #005fff  #000000  #020204
        client.placeholder       #000000ee  #000000    #ffffff  #000000  #0c0c0c
        client.unfocused         #000000ee  #000000    #315c70  #000000  #020204
        client.urgent            #000000ee  #2E2457    #4C407C  #32275E  #32275E
    '''
    )

    mode_default = Δ(
        exec = λ({
            (f'{M4}+4') : '~/bin/screenshot',
            (f'{M4}+{Ct}+4') : '~/bin/screenshot -r',
            (f'{M4}+{Sh}+4') : 'flameshot gui',
        }, fmt='exec {cmd}'),

        exec_no_startup_id = λ({
            (f'{M1}+grave') : 'rofi -show run -show-icons -disable-history -theme neg',
            (f'{M4}+8') : 'playerctl volume 0.0 || amixer -q set Master 0 mute',
            (f'{M4}+c') : '~/bin/clip',
            (f'{M4}+g') : '~/bin/g',
            (f'{M4}+p') : '~/bin/rofi-tmux-urls',
            (f'{M4}+m') : '~/bin/music-rename current',
            (f'{M4}+{Sh}+6') : '~/bin/wl',
            (f'{M4}+{Sh}+8') : 'playerctl volume 1.0 || amixer -q set Master 65536 unmute',
            (f'{M4}+{Sh}+9') : 'dunstctl history-pop',
            (f'{M4}+{Sh}+i') : '~/bin/rofi-nm',
            (f'{M4}+{Sh}+l') : '~/bin/rofi-lutris',
            (f'{M4}+{Sh}+m') : '~/bin/rofi-audio',
            (f'{M4}+{Sh}+y') : '~/bin/clip youtube-dw-list',
            (f'{M4}+space') : 'dunstctl close-all',
            ('XF86Sleep') : 'sudo systemctl suspend',
        }, fmt='exec --no-startup-id {cmd}'),

        focus = λ({
            (f'{M4}+j') : 'down',
            (f'{M4}+h') : 'left',
            (f'{M4}+l') : 'right',
            (f'{M4}+k') : 'up',
        }, fmt='focus {cmd}'),

        i3 = λ({
            (f'{M4}+apostrophe') : 'reload',
            (f'{M4}+{Sh}+apostrophe') : 'restart'
        }),

        vol = λ({
            ('XF86AudioLowerVolume') : 'd',
            ('XF86AudioRaiseVolume') : 'u',
        }, fmt='$vol {cmd}'),

        remember_focused = λ({
            (f'{M4}+grave') : 'focus_next_visible',
            (f'{M4}+{Sh}+grave') : 'focus_prev_visible',
            (f'{M1}+Tab'): 'switch',
            (f'{M4}+slash') : 'switch',
        }, fmt='$remember_focused {cmd}'),

        scratchpad = λ({
            (f'{M4}+{Ct}+a') : 'dialog',
            (f'{M4}+{Ct}+s') : 'geom_dump',
            (f'{M4}+{Ct}+space') : 'geom_restore',
            (f'{M4}+s') : 'hide_current',
            (f'{M4}+3') : 'next',
        }, fmt='$scratchpad {cmd}'),

        media = λ({
            (f'{M4}+period') : 'next',
            (f'{M4}+{Sh}+2') : 'play-pause',
            (f'{M4}+comma') : 'previous',
        }, fmt='exec --no-startup-id playerctl {cmd}'),

        media_xf86 = λ({
            ('XF86AudioNext') : 'next',
            ('XF86AudioPlay') : 'play',
            ('XF86AudioPrev') : 'previous',
            ('XF86AudioStop') : 'stop',
        }, fmt='exec --no-startup-id playerctl {cmd}'),

        menu = λ({
            (f'{M4}+{Sh}+a') : 'attach',
            (f'{M4}+{Sh}+s') : 'autoprop',
            (f'{M4}+{Ct}+grave') : 'cmd_menu',
            (f'{M1}+g') : 'goto_win',
            (f'{M4}+{Ct}+g') : 'movews',
            (f'{M1}+{Ct}+g') : 'ws',
        }, fmt='$menu {cmd}'),

        misc = λ({
            (f'{M4}+q') : 'fullscreen toggle',
            (f'{M4}+{Ct}+q') : 'kill',
        }),
    )

    mode_resize = Δ(bind=f'{M4}+r',
        plus = λ({
            'bottom' : ['j', 's'],
            'left' : ['h', 'a'],
            'right' : ['l', 'd'],
            'top' : ['k', 'w'],
        }, fmt='$actions resize {cmd} 4'),

        minus = λ({
            'bottom' : [f'{Sh}+j', f'{Sh}+s'],
            'left' : [f'{Sh}+h', f'{Sh}+a'],
            'right' : [f'{Sh}+l', f'{Sh}+d'],
            'top' : [f'{Sh}+k', f'{Sh}+w'],
        }, fmt='$actions resize {cmd} -4'),
    )

    mode_spec = Δ(bind=f'{M1}+e',
        misc = λ({
            ('e') : '[urgent=latest] focus',
            ('l') : 'exec i3lockr -p 8 ',
            (f'{Sh}+d') : 'floating toggle',
        }, exit=True),

        menu = λ({
            (f'{Sh}+t') : 'gtk_theme',
            (f'{Sh}+i') : 'icon_theme',
            ('i') : 'pulse_input',
            ('o') : 'pulse_output',
            ('m') : 'xprop_show',
        }, fmt='$menu {cmd}', exit=True),
    )

    mode_wm = Δ(bind=f'{M4}+minus',
        layout = λ({
            (f'grave') : 'default',
            (f'minus') : 'splith',
            (f'backslash') : 'splitv',
            (f't') : 'tabbed',
            (f'{Ct}+t') : 'toggle',
        }, fmt='layout {cmd}', exit=True),

        split = λ({
            'horizontal' : ['h', 'l'],
            'vertical' : ['j', 'k'],
        }, fmt='split', exit=True),

        move = λ({
            ('w') : 'top',
            ('a') : 'left',
            ('s') : 'bottom',
            ('d') : 'right',
        }, fmt='move {cmd}'),

        actions = λ({
            (f'{Sh}+plus') : 'grow',
            ('x') : 'maxhor',
            ('m') : 'maximize',
            ('y') : 'maxvert',
            ('c') : 'none',
            (f'{Sh}+c') : 'resize',
            'revert_maximize' : [f'{Sh}+m', f'{Sh}+x', f'{Sh}+y'],
            'shrink' : [f'{Sh}+minus'],
        }, fmt='$actions'),

        actions_x2 = λ({
            'hdown' : [f'{Sh}+w'],
            'hup' : [f'{Sh}+a'],
            'vleft' : [f'{Sh}+s'],
            'vright' : [f'{Sh}+d'],
        }, fmt='$actions {cmd} x2'),
    )
