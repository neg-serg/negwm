from enum import Enum
Δ = dict


class circle(Enum):
    bitwig = Δ(
        classw = ['Bitwig Studio'],
        keybind_next = ['Mod4+Control+b'],
        prog = 'bitwig-studio',
        ws = 'sound'
    )

    doc = Δ(
        classw = ['Zathura', 'cr3'],
        keybind_next = ['Mod4+o'],
        ws = 'doc'
    )

    nwim = Δ(
        classw = ['nwim'],
        keybind_next = ['Mod4+1'],
        spawn = 'nwim',
        ws = 'dev'
    )

    obs = Δ(
        classw = ['obs'],
        keybind_toggle = ['Mod4+Shift+o'],
        prog = 'obs',
        ws = 'obs'
    )

    remote = Δ(
        classw = ['xfreerdp', 'reminna', 'org.remmina.Remmina'],
        keybind_toggle = ['Mod4+Control+5'],
        ws = 'remote'
    )

    steam = Δ(
        classw = ['Steam', 'steam'],
        keybind_next = ['Mod4+Shift+e'],
        prog = 'zsh -c "flatpak run com.valvesoftware.Steam"',
        ws = 'steam'
    )

    nsxiv = Δ(
        classw = ['Nsxiv'],
        keybind_next = ['Mod4+Control+c'],
        prog = "~/bin/sx ~/dw/ ~/tmp/shots/",
        wallpaper = {'classw': ['Nsxiv'], 'keybind_subtag': ['Mod4+Shift+c'], 'prog': '~/bin/wl --show'},
        ws = 'gfx'
    )

    term = Δ(
        instance = ['term'],
        keybind_next = ['Mod4+x'],
        spawn = 'term',
        ws = 'term'
    )

    vid = Δ(
        classw = ['mpv'],
        keybind_next = ['Mod4+b'],
        mpd_shut = 0,
        prog = '~/bin/pl rofi 1st_level ~/vid/new',
        ws = 'gfx'
    )

    vm = Δ(
        classw = ['spicy'],
        class_r = ['^[Qq]emu-.*$'],
        keybind_next = ['Mod4+Control+v'],
        ws = 'vm'
    )

    web = Δ(
        classw = ['firefox', 'firefoxdeveloperedition', 'Tor Browser', 'Chromium'],
        keybind_next = ['Mod4+w'],
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
