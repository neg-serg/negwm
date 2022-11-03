""" Dynamic S-expressions based config for negwm.

This is a superclass for negwm which want to store configuration via hy
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import sys
import pickle
import traceback
import logging
from typing import Set, Any, Dict, List
from negwm.lib.misc import Misc
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

    @staticmethod
    def cfg_regex_props() -> Set[str]:
        """ Props with regexes """
        return {"class_r", "instance_r", "name_r", "role_r"}

    @staticmethod
    def cfg_props() -> Set[str]:
        """ Basic cfg properties, without regexes """
        return {'classw', 'instance', 'name', 'role'}

    @staticmethod
    def subtag_attr_list() -> Set[str]:
        """ Helper to create subtag attr list. """
        return {'class', 'instance', 'window_role', 'title'}

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

    def property_to_winattrib(self, prop_str: str) -> None:
        """ Parse property string to create win_attrs dict.
            prop_str (str): property string in special format. """
        self.win_attrs={}
        prop_str=prop_str[1:-1]
        for token in prop_str.split('@'):
            if token:
                toks=token.split('=')
                attr, value=toks[0], toks[1]
                if value[0] == value[-1] and value[0] in {'"', "'"}:
                    value=value[1:-1]
                if attr in cfg.subtag_attr_list():
                    self.win_attrs[cfg.props(attr)]=value

    def add_props(self, tag: str, prop_str: str) -> None:
        """ Move window to some tag.
            tag (str): target tag
            prop_str (str): property string in special format. """
        self.property_to_winattrib(prop_str)
        config=self.cfg
        ftors=cfg.cfg_props() & set(self.win_attrs.keys())
        if tag in config:
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

    def del_direct_props(self, target_tag: str) -> None:
        """ Remove basic(non-regex) properties of window from target tag.
            tag (str): target tag """
        config=self.cfg
        for prop in config[target_tag].copy():
            if prop in cfg.cfg_props():
                if isinstance(self.conf(target_tag, prop), str):
                    del config[target_tag][prop]
                elif isinstance(self.conf(target_tag, prop), set):
                    for tok in config[target_tag][prop].copy():
                        if self.win_attrs[prop] == tok:
                            config[target_tag][prop].remove(tok)

    def del_regex_props(self, target_tag: str) -> None:
        """ Remove regex properties of window from target tag.
            target_tag (str): target tag """
        config=self.cfg
        def check_for_win_attrs(win, prop):
            class_r_check=(prop == "class_r" and winattr == win.window_class)
            instance_r_check=(prop == "instance_r" and winattr == win.window_instance)
            role_r_check=(prop == "role_r" and winattr == win.window_role)
            if class_r_check or instance_r_check or role_r_check:
                config[target_tag][prop].remove(target_tag)
        lst_by_reg=[]
        # Delete appropriate regexes
        tree=self.i3ipc.get_tree()
        for prop in config[target_tag].copy():
            if prop in cfg.cfg_regex_props():
                for reg in config[target_tag][prop].copy():
                    if prop == "class_r": lst_by_reg=tree.find_classed(reg)
                    if prop == "instance_r": lst_by_reg=tree.find_instanced(reg)
                    if prop == "role_r": lst_by_reg=tree.find_by_role(reg)
                    winattr=self.win_attrs[prop[:-2]]
                    for win in lst_by_reg: check_for_win_attrs(win, prop)

    def del_props(self, tag: str, prop_str: str) -> None:
        """ Remove window from some tag.
        tag (str): target tag
        prop_str (str): property string in special format. """
        self.property_to_winattrib(prop_str)
        self.del_direct_props(tag)
        self.del_regex_props(tag)
        config=self.cfg
        # Cleanup
        for prop in cfg.cfg_regex_props() | self.cfg_props():
            if prop in self.conf(tag) and self.conf(tag, prop) == set():
                del config[tag][prop]
