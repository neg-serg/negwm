from enum import Enum

class Executor(Enum):
    ncmpcpp = {
        'class': 'ncmpcpp',
        'exec': 'ncmpcpp',
        'font': 'Iosevka',
        'font_normal': 'Medium',
        'font_size': 27,
        'opacity': 0.8,
        'padding': [12, 12]
    }

    neomutt = {
        'class': 'neomutt',
        'exec_dtach': 'neomutt',
        'font': 'Iosevka',
        'font_size': 27
    }

    nwim = {
        'class': 'nwim',
        'env': ['NVIM_LISTEN_ADDRESS=/tmp/nvimsocket'],
        'exec_tmux': [['nvim', '/usr/bin/nvim']],
        'font': 'Iosevka',
        'font_normal': 'Medium',
        'font_size': 27.5,
        'opacity': 0.95,
        'padding': [8, 8],
        'statusline': 0
    }

    teardrop = {
        'class': 'teardrop',
        'exec_tmux': [['top', '/usr/bin/bpytop']],
        'font': 'Iosevka',
        'font_size': 20,
        'padding': [8, 8],
        'statusline': 0
    }

    term = {
        'class': 'term',
        'exec_tmux': [['zsh', 'zsh']],
        'font': 'Iosevka',
        'font_size': 33,
        'padding': [8, 8],
        'statusline': 1
    }
