""" Config for NegWM modules
This is a superclass for negwm which want to store configuration via hy files. It supports inotify-based updating of self.cfg dynamically
and has pretty simple API. I've considered that inheritance here is good idea. """

import sys
import traceback
import logging
from typing import Any, Dict, List
import ruamel.yaml as yaml
from negwm.lib.misc import Misc
from negwm.lib.extension import extension


class NewLineDumper(yaml.Dumper):
    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


class cfg():
    def __init__(self, i3) -> None:
        self.mod=self.__class__.__name__    # detect current extension
        self.cfg_path=f'{Misc.cfg_path()}/{self.mod}.cfg'
        self.load_config()                  # load current config
        self.win_attrs={}                   # used for props add / del hacks
        self.additional_props=[dict()]      # used to store add_prop history
        if not self.cfg: self.cfg={}
        self.i3ipc=i3

    def get_config(self) -> Dict: return self.cfg
    def get_added_props(self) -> List: return self.additional_props

    def conf(self, *conf_path) -> Any:
        """ Helper to extract config for current tag. conf_path: path of config
        from where extract. """
        ret={}
        for part in conf_path:
            if not ret:
                ret=self.cfg.get(part)
            else:
                ret=ret.get(part)
                return ret
        return ret

    def reload(self, *_) -> None:
        """ Reload config for current selected module. Call load_config, print
        debug messages and reinit all stuff. """
        prev_conf=self.cfg
        try:
            self.load_config()
            self.__init__(self.i3ipc)
            extensions=extension.get_mods()
            if 'configurator' in extensions:
                getattr(extensions['configurator'], 'write')()
            logging.info(f"[{self.mod}] config reloaded")
            print(f"[{self.mod}] config reloaded")
        except Exception:
            logging.info(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg=prev_conf
            self.__init__(*_)

    def load_config(self) -> None:
        """ Reload config """
        try:
            y=yaml.YAML(typ='rt')
            y.preserve_quotes=True
            with open(self.cfg_path, "r") as mod_cfg:
                self.cfg=y.load(mod_cfg)
        except FileNotFoundError:
            logging.error(f'file {self.cfg_path} not exists')

    def dump_config(self) -> None:
        """ Dump current config, can be used for debugging. """
        with open(self.cfg_path, "w+") as mod_cfg:
            y=yaml.YAML(typ='rt')
            y.allow_unicode=True
            y.dump(self.cfg, mod_cfg, Dumper=NewLineDumper, width=140)
