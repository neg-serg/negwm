#!/usr/bin/env python3
import pickle
import glob
import pathlib
from negwm.lib.misc import Misc

from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader


class Configs():
    def __init__(self):
        self.config={}
        extension='cfg'
        config_list=map(pathlib.Path, glob.glob(f"{Misc.cfg_path()}/*.{extension}"))
        for conf in config_list:
            if conf.is_file():
                conf_name=conf.name.removesuffix(f'.{extension}')
                spec=spec_from_loader(conf_name, SourceFileLoader(conf_name, str(conf)))
                if spec is not None and spec.loader is not None:
                    cfg=module_from_spec(spec)
                    spec.loader.exec_module(cfg)
                    self.config[conf_name]=getattr(cfg,conf_name)

    def dump(self):
        cfg_dir=f'{Misc.cfg_path()}'
        Misc.create_dir(cfg_dir)
        Misc.create_dir(f'{Misc.cache_path()}')
        for mod_name, raw_config in self.config.items():
            mod_config={}
            for elem in raw_config:
                mod_config.update({elem.name: elem.value})
            i3_cfg_mod_path=f'{Misc.cache_path()}/{mod_name}.pickle'
            with open(i3_cfg_mod_path, "wb") as mod_cfg:
                pickle.dump(mod_config, mod_cfg)

if __name__ == '__main__':
    Configs().dump()
