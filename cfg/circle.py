from enum import Enum
Δ = dict


class circle(Enum):
    bitwig = Δ(
        classw = ['Bitwig Studio'],
        keybind_default_next = ['Mod4+Control+b'],
        prog = 'bitwig-studio',
        ws = 'sound'
    )

    doc = Δ(
        classw = ['Zathura', 'cr3'],
        keybind_default_next = ['Mod4+o'],
        ws = 'doc'
    )

    lutris = Δ(
        classw = ['Wine', 'Lutris'],
        keybind_default_next = ['Mod4+Control+e'],
        prog = 'lutris',
        ws = 'steam'
    )

    nwim = Δ(
        instance = ['nwim'],
        keybind_default_next = ['Mod4+1'],
        spawn = 'nwim',
        ws = 'dev'
    )

    obs = Δ(
        classw = ['obs'],
        keybind_default_toggle = ['Mod4+Shift+o'],
        prog = 'obs',
        ws = 'obs'
    )

    remote = Δ(
        classw = ['xfreerdp', 'reminna', 'org.remmina.Remmina'],
        keybind_default_toggle = ['Mod4+Control+5'],
        ws = 'remote'
    )

    steam = Δ(
        classw = ['Steam', 'steam'],
        keybind_default_next = ['Mod4+Shift+e'],
        prog = 'steam',
        ws = 'steam'
    )

    sxiv = Δ(
        classw = ['Sxiv'],
        keybind_default_next = ['Mod4+Control+c'],
        prog = "dash -c 'exec find ~/dw/ ~/tmp/shots/ -maxdepth 1 -type d -print0 | xargs -0 ~/bin/sx'",
        wallpaper = {'classw': ['Sxiv'], 'keybind_default_subtag': ['Mod4+Shift+c'], 'prog': '~/bin/wl --show'},
        ws = 'gfx'
    )

    term = Δ(
        instance = ['term'],
        keybind_default_next = ['Mod4+x'],
        spawn = 'term',
        ws = 'term'
    )

    vid = Δ(
        classw = ['mpv'],
        keybind_default_next = ['Mod4+b'],
        mpd_shut = 0,
        prog = '~/bin/pl rofi 1st_level ~/vid/new',
        ws = 'gfx'
    )

    vm = Δ(
        classw = ['spicy'],
        class_r = ['^[Qq]emu-.*$'],
        keybind_default_next = ['Mod4+Control+v'],
        ws = 'vm'
    )

    web = Δ(
        classw = ['firefox', 'firefoxdeveloperedition', 'Tor Browser', 'Chromium'],
        keybind_default_next = ['Mod4+w'],
        prog = 'firefox',
        firefox = Δ(
            classw = ['firefox'],
            keybind_spec_subtag = ['f'],
            prog = 'firefox'
        ),
        tor = Δ(
            classw = ['Tor Browser'],
            keybind_spec_subtag = ['5'],
            prog = 'tor-browser rutracker.org'
        ),
        ws = 'web'
    )
