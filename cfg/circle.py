from enum import Enum

class circle(Enum):
    bitwig = dict(
        classw = ['Bitwig Studio'],
        keybind_default_next = ['Mod4+Control+b'],
        prog = 'bitwig-studio',
        ws = 'sound'
    )

    doc = dict(
        classw = ['Zathura', 'cr3'],
        keybind_default_next = ['Mod4+o'],
        ws = 'doc'
    )

    lutris = dict(
        classw = ['Wine', 'Lutris'],
        keybind_default_next = ['Mod4+Control+e'],
        prog = 'lutris',
        ws = 'steam'
    )

    nwim = dict(
        instance = ['nwim'],
        keybind_default_next = ['Mod4+1'],
        spawn = 'nwim',
        ws = 'dev'
    )

    obs = dict(
        classw = ['obs'],
        keybind_default_toggle = ['Mod4+Shift+o'],
        prog = 'obs',
        ws = 'obs'
    )

    remote = dict(
        classw = ['xfreerdp', 'reminna', 'org.remmina.Remmina'],
        keybind_default_toggle = ['Mod4+Control+5'],
        ws = 'remote'
    )

    steam = dict(
        classw = ['Steam', 'steam'],
        keybind_default_next = ['Mod4+Shift+e'],
        prog = 'steam',
        ws = 'steam'
    )

    sxiv = dict(
        classw = ['Sxiv'],
        keybind_default_next = ['Mod4+Control+c'],
        prog = "dash -c 'exec find ~/dw/ ~/tmp/shots/ -maxdepth 1 -type d -print0 | xargs -0 ~/bin/sx'",
        wallpaper = {'classw': ['Sxiv'], 'keybind_default_subtag': ['Mod4+Shift+c'], 'prog': '~/bin/wl --show'},
        ws = 'gfx'
    )

    term = dict(
        instance = ['term'],
        keybind_default_next = ['Mod4+x'],
        spawn = 'term',
        ws = 'term'
    )

    vid = dict(
        classw = ['mpv'],
        keybind_default_next = ['Mod4+b'],
        mpd_shut = 0,
        prog = '~/bin/pl rofi 1st_level ~/vid/new',
        ws = 'gfx'
    )

    vm = dict(
        classw = ['spicy'],
        class_r = ['^[Qq]emu-.*$'],
        keybind_default_next = ['Mod4+Control+v'],
        ws = 'vm'
    )

    web = dict(
        classw = ['firefox', 'firefoxdeveloperedition', 'Tor Browser', 'Chromium'],
        keybind_default_next = ['Mod4+w'],
        prog = 'MOZ_X11_EGL=1 MOZ_ACCELERATED=1 MOZ_WEBRENDER=1 firefox-developer-edition',
        firefox = dict(
            classw = ['firefox'],
            keybind_spec_subtag = ['f'],
            prog = 'MOZ_X11_EGL=1 MOZ_ACCELERATED=1 MOZ_WEBRENDER=1 firefox'
        ),
        tor = dict(
            classw = ['Tor Browser'],
            keybind_spec_subtag = ['5'],
            prog = 'tor-browser rutracker.org'
        ),
        ws = 'web'
    )
