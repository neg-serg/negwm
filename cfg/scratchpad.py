from enum import Enum

class Scratchpad(Enum):
    discord = {
        'class': ['discord'],
        'geom': '1888x2072+1948+254',
        'keybind_default_toggle': ['Mod4+v'],
        'prog': 'discord'
    }

    im = {
        'class': ['zoom', 'KotatogramDesktop', 'Slack', 'TelegramDesktop', 'Skype', 'myteam'],
        'geom': '1304x2109+2536+2',
        'keybind_default_toggle': ['Mod4+e'],
        'tel': {
            'class': ['KotatogramDesktop'],
            'keybind_spec_subtag': ['t'],
            'prog': 'kotatogram-desktop'
        }
    }

    ncmpcpp = {
        'geom': '2266x932+846+748',
        'instance': ['ncmpcpp'],
        'keybind_default_toggle': ['Mod4+f'],
        'spawn': 'ncmpcpp',
    }

    neomutt = {
        'class': ['mutterfox'],
        'geom': '3670x2228+104+0',
        'instance': ['mutterfox', 'neomutt'],
        'keybind_default_toggle': ['Mod4+n'],
        'spawn': 'neomutt',
    }

    password = {
        'geom': '1690x838+2150+1272',
        'instance': ['1password'],
        'keybind_default_toggle': ['Mod4+Control+p'],
        'prog': '1password'
    }

    teardrop = {
        'geom': '3840x1300+0+0',
        'instance': ['teardrop'],
        'keybind_default_toggle': ['Mod4+d'],
        'spawn': 'teardrop'
    }

    transients = {
        'geom': '1812x797+693+1310',
        'match_all': ['True'],
        'role': ['GtkFileChooserDialog', 'Organizer', 'Manager']
    }

    webcam = {
        'geom': '2463x1880+1368+268',
        'instance': ['webcam'],
        'keybind_spec_toggle': ['w'],
        'prog': '~/bin/webcam'
    }
