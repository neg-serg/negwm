from enum import Enum
Δ = dict


class scratchpad(Enum):
    discord = Δ(
        classw = ['discord'],
        geom = '1898x1273+1936+825',
        keybind_toggle = ['Mod4+v'],
        prog = 'discord'
    )

    im = Δ(
        classw = ['KotatogramDesktop', 'vkteams', 'Skype', 'Slack', 'TelegramDesktop', 'zoom'],
        geom = '1304x2109+2536+2',
        keybind_toggle = ['Mod4+e'],
        tel = Δ(
            classw = ['KotatogramDesktop'],
            keybind_spec_subtag = ['t'],
            prog = 'kotatogram-desktop'
        )
    )

    ncmpcpp = Δ(
        geom = '2251x852+753+1181',
        classw = ['ncmpcpp'],
        keybind_toggle = ['Mod4+f'],
        spawn = 'ncmpcpp',
    )

    neomutt = Δ(
        classw = ['mutterfox'],
        geom = '3670x2228+104+0',
        instance = ['mutterfox', 'neomutt'],
        keybind_toggle = ['Mod4+n'],
        spawn = 'neomutt',
    )

    password = Δ(
        geom = '1690x838+2150+1272',
        instance = ['1password'],
        keybind_toggle = ['Mod4+Control+p'],
        prog = '1password'
    )

    teardrop = Δ(
        geom = '3840x1300+0+0',
        instance = ['teardrop'],
        keybind_toggle = ['Mod4+d'],
        spawn = 'teardrop'
    )

    torrment = Δ(
        geom = '3840x1300+0+0',
        instance = ['torrment'],
        keybind_toggle = ['Mod4+t'],
        spawn = 'torrment'
    )

    transients = Δ(
        geom = '1812x797+693+1310',
        match_all = ['True'],
        role = ['GtkFileChooserDialog', 'Organizer', 'Manager']
    )

    webcam = Δ(
        geom = '2463x1880+1368+268',
        instance = ['webcam'],
        keybind_spec_toggle = ['w'],
        prog = '~/bin/webcam'
    )
