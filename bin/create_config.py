#!/usr/bin/python3
import sys
sys.path.append("../cfg")
sys.path.append("../lib")
import pickle
from misc import Misc

from fullscreen import Fullscreen
from executor import Executor
from actions import Actions
from circle import Circle
from remember_focused import RememberFocused
from menu import Menu
from scratchpad import Scratchpad
from conf_gen import ConfGen
from negi3wm import Negi3wm

class Configs():
    def __init__(self):
        self.config = {}
        self.config = {
            'fullscreen': Fullscreen,
            'executor': Executor,
            'actions': Actions,
            'circle': Circle,
            'remember_focused': RememberFocused,
            'menu': Menu,
            'scratchpad': Scratchpad,
            'conf_gen': ConfGen,
            'negi3wm': Negi3wm,
        }

    def print(self):
        for mod_name, config in self.config.items():
            print()
            print(f'{mod_name} :: ')
            mod_config = {}
            for elem in config:
                mod_config.update({elem.name: elem.value})
            print(mod_config)
            print()

    def dump(self):
        for mod_name, raw_config in self.config.items():
            mod_config = {}
            for elem in raw_config:
                mod_config.update({elem.name: elem.value})
            i3_cfg_mod_path = f'{Misc.i3path()}/cache/cfg/{mod_name}.pickle'
            with open(i3_cfg_mod_path, "wb") as mod_cfg:
                pickle.dump(mod_config, mod_cfg)

Configs().dump()
