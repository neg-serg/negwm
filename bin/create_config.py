#!/usr/bin/env python3
import sys
import importlib
import pickle
import glob
import pathlib
import logging
sys.path.append("../cfg")
sys.path.append("../lib")
sys.path.append("..")
from lib.misc import Misc


class Configs():
    def __init__(self):
        self.config = {}
        extension = 'py'
        config_list = map(pathlib.Path, glob.glob(f"{Misc.cfg_path}/*.{extension}"))
        for conf in config_list:
            if conf.is_file():
                conf_name = conf.name.removesuffix(f'.{extension}')
                self.config[conf_name] = getattr(
                    importlib.import_module(conf_name),
                    conf_name
                )

    def print(self):
        for mod_name, config in self.config.items():
            logging.info(f'\n{mod_name} :: ')
            mod_config = {}
            for elem in config:
                mod_config.update({elem.name: elem.value})
            logging.info(f'mod_config\n')

    def dump(self):
        for mod_name, raw_config in self.config.items():
            mod_config = {}
            for elem in raw_config:
                mod_config.update({elem.name: elem.value})
            i3_cfg_mod_path = f'{Misc.cache_path()}/cfg/{mod_name}.pickle'
            with open(i3_cfg_mod_path, "wb") as mod_cfg:
                pickle.dump(mod_config, mod_cfg)

Configs().dump()
