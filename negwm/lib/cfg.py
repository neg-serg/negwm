""" Dynamic S-expressions based config for negwm.

This is a superclass for negwm which want to store configuration via hy
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import sys
import pickle
import traceback
import logging
from typing import Any, Dict, List
from negwm.lib.misc import Misc
from negwm.lib.props import props
from negwm.lib.extension import extension


class cfg():
    @staticmethod
    def props(prop):
        if prop == 'title': return 'name'
        else: return prop

    def __init__(self, i3) -> None:
        self.mod=self.__class__.__name__ # detect current extension
        # extension config path
        self.negwm_mod_cfg_cache_path=f'{Misc.cache_path()}/cfg/{self.mod}.pickle'
        self.load_config() # load current config
        self.win_attrs={} # used for props add / del hacks
        self.additional_props=[dict()] # used to store add_prop history
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
            if 'conf_gen' in extensions:
                getattr(extensions['conf_gen'], 'write')()
            logging.info(f"[{self.mod}] config reloaded")
            print(f"[{self.mod}] config reloaded")
        except Exception:
            logging.info(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg=prev_conf
            self.__init__(*_)

    def load_config(self) -> None:
        """ Reload config itself and convert lists in it to sets for the better
        performance. """
        try:
            with open(self.negwm_mod_cfg_cache_path, "rb") as mod_cfg:
                self.cfg=pickle.load(mod_cfg)
        except FileNotFoundError:
            logging.error(f'file {self.negwm_mod_cfg_cache_path} not exists')

    def dump_config(self) -> None:
        """ Dump current config, can be used for debugging. """
        with open(self.negwm_mod_cfg_cache_path, "wb") as mod_cfg:
            pickle.dump(self.cfg, mod_cfg)

    def add_props(self, tag: str, prop_str: str) -> None:
        """ Move window to some tag.
            tag (str): target tag
            prop_str (str): property string in special format. """
        props.property_to_winattrib(self.win_attrs, prop_str)
        config=self.cfg
        ftors=props.cfg_props() & set(self.win_attrs.keys())
        if not tag in config:
            return
        for tok in ftors:
            if self.win_attrs[tok] not in config.get(tag, {}).get(tok, {}):
                if tok in config[tag]:
                    if isinstance(config[tag][tok], str):
                        config[tag][tok]={self.win_attrs[tok]}
                    elif isinstance(config[tag][tok], list):
                        config[tag][tok].append(self.win_attrs[tok])
                        config[tag][tok]=list(dict.fromkeys(config[tag][tok]))
                else:
                    config[tag].update({tok: self.win_attrs[tok]})
                # fix for the case where attr is just attr not {attr}
                if isinstance(self.conf(tag, tok), str):
                    config[tag][tok]={self.win_attrs[tok]}
        self.additional_props.append({
            'mod': self.__class__.__name__,
            'tag': tag,
            'prop': prop_str})
        self.additional_props=list(filter(len, self.additional_props))

    def del_props(self, tag: str, prop_str: str) -> None:
        """ Remove window from some tag.
        tag (str): target tag
        prop_str (str): property string in special format. """
        tree=self.i3ipc.get_tree()
        props.property_to_winattrib(self.win_attrs, prop_str)
        props.del_direct_props(self.cfg, self.win_attrs, tag)
        props.del_regex_props(self.cfg, tree, self.win_attrs, tag)
        config=self.cfg
        for prop in props.cfg_regex_props() | props.cfg_props():
            if prop in self.conf(tag) and self.conf(tag, prop) == set():
                del config[tag][prop]
