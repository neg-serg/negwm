""" Dynamic TOML-based config for negi3wm.

This is a superclass for negi3wm which want to store configuration via TOML
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import re
import os
import sys
import qtoml
import traceback
from typing import Set, Callable
from lib.misc import Misc


class cfg():
    def __init__(self, i3) -> None:
        self.mod = self.__class__.__name__ # detect current extension
        # extension config path
        self.i3_cfg_mod_path = Misc.i3path() + '/cfg/' + self.mod + '.toml'
        self.load_config() # load current config
        self.win_attrs = {} # used for props add / del hacks
        self.conv_props = {
            'class': 'class',
            'instance': 'instance',
            'window_role': 'window_role',
            'title': 'name',
        }
        if not self.cfg:
            self.cfg = {}
        self.i3ipc = i3

    def conf(self, *conf_path):
        """ Helper to extract config for current tag. conf_path: path of config
        from where extract. """
        ret = {}
        for part in conf_path:
            if not ret:
                ret = self.cfg.get(part)
            else:
                ret = ret.get(part)
                return ret
        return ret

    @staticmethod
    def extract_prog_str(conf_part: dict,
                         prog_field: str = "prog",
                         exe_file: bool = True) -> str:
        """ Helper to extract prog(by default) string from config
            conf_part (dict): part of config from where you want to extract it.
            prog_field (str): string name to extract.
        """
        if conf_part is None:
            return ""
        if exe_file:
            return re.sub(
                "~",
                os.path.realpath(os.path.expandvars("$HOME")),
                conf_part.get(prog_field, "")
            )
        return conf_part.get(prog_field, "")

    @staticmethod
    def cfg_regex_props() -> Set[str]:
        """ Props with regexes """
        return {"class_r", "instance_r", "name_r", "role_r"}

    def win_all_props(self):
        """ Basic + regex props """
        return self.cfg_props() | self.cfg_regex_props()

    @staticmethod
    def possible_props() -> Set[str]:
        """ Windows properties used for props add / del """
        return {'class', 'instance', 'window_role', 'title'}

    @staticmethod
    def cfg_props() -> Set[str]:
        """ Basic cfg properties, without regexes """
        return {'class', 'instance', 'name', 'role'}

    @staticmethod
    def subtag_attr_list() -> Set[str]:
        """ Helper to create subtag attr list. """
        return cfg.possible_props()

    def reload_config(self, *_) -> None:
        """ Reload config for current selected module. Call load_config, print
        debug messages and reinit all stuff. """
        prev_conf = self.cfg
        try:
            self.load_config()
            self.__init__(self.i3ipc)
            print(f"[{self.mod}] config reloaded")
        except Exception:
            print(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__(*_)

    def dict_apply(self, field_conv: Callable, subtag_conv: Callable) -> None:
        """ Convert list attributes to set for the better performance.
            field_conv (Callable): function to convert dict field.
            subtag_conv (Callable): function to convert subtag inside dict. """
        for string in self.cfg.values():
            for key in string:
                if key in self.win_all_props():
                    string[sys.intern(key)] = field_conv(
                        string[sys.intern(key)]
                    )
                elif key == "subtag":
                    subtag_conv(string[sys.intern(key)])

    @staticmethod
    def subtag_apply(subtag, field_conv: Callable) -> None:
        """ Convert subtag attributes to set for the better performance.
            subtag (str): target subtag name.
            field_conv (Callable): function to convert dict field. """
        for val in subtag.values():
            for key in val:
                if key in cfg.subtag_attr_list():
                    val[sys.intern(key)] = field_conv(val[sys.intern(key)])

    def load_config(self) -> None:
        """ Reload config itself and convert lists in it to sets for the better
        performance. """
        try:
            with open(self.i3_cfg_mod_path, "r") as mod_cfg:
                self.cfg = qtoml.load(mod_cfg)
        except FileNotFoundError:
            print(f'file {self.i3_cfg_mod_path} not exists')

    def dump_config(self) -> None:
        """ Dump current config, can be used for debugging. """
        with open(self.i3_cfg_mod_path, "r+") as mod_cfg:
            print(self.cfg)
            qtoml.dump(self.cfg, mod_cfg)
            self.cfg = qtoml.load(mod_cfg)

    def property_to_winattrib(self, prop_str: str) -> None:
        """ Parse property string to create win_attrs dict.
            prop_str (str): property string in special format. """
        self.win_attrs = {}
        prop_str = prop_str[1:-1]
        for token in prop_str.split('@'):
            if token:
                toks = token.split('=')
                attr = toks[0]
                value = toks[1]
                if value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                if attr in cfg.subtag_attr_list():
                    self.win_attrs[self.conv_props.get(attr, {})] = value

    def add_props(self, tag: str, prop_str: str) -> None:
        """ Move window to some tag.
            tag (str): target tag
            prop_str (str): property string in special format. """
        self.property_to_winattrib(prop_str)
        ftors = self.cfg_props() & set(self.win_attrs.keys())
        if tag in self.cfg:
            for tok in ftors:
                if self.win_attrs[tok] not in \
                        self.cfg.get(tag, {}).get(tok, {}):
                    if tok in self.cfg[tag]:
                        if isinstance(self.cfg[tag][tok], str):
                            self.cfg[tag][tok] = {self.win_attrs[tok]}
                        elif isinstance(self.cfg[tag][tok], list):
                            self.cfg[tag][tok].append(self.win_attrs[tok])
                            self.cfg[tag][tok] = list(
                                dict.fromkeys(self.cfg[tag][tok])
                            )
                    else:
                        self.cfg[tag].update({tok: self.win_attrs[tok]})
                    # fix for the case where attr is just attr not {attr}
                    if isinstance(self.conf(tag, tok), str):
                        self.cfg[tag][tok] = {self.win_attrs[tok]}

    def del_direct_props(self, target_tag: str) -> None:
        """ Remove basic(non-regex) properties of window from target tag.
            tag (str): target tag """
        # Delete 'direct' props:
        for prop in self.cfg[target_tag].copy():
            if prop in self.cfg_props():
                if isinstance(self.conf(target_tag, prop), str):
                    del self.cfg[target_tag][prop]
                elif isinstance(self.conf(target_tag, prop), set):
                    for tok in self.cfg[target_tag][prop].copy():
                        if self.win_attrs[prop] == tok:
                            self.cfg[target_tag][prop].remove(tok)

    def del_regex_props(self, target_tag: str) -> None:
        """ Remove regex properties of window from target tag.
            target_tag (str): target tag """
        def check_for_win_attrs(win, prop):
            class_r_check = \
                (prop == "class_r" and winattr == win.window_class)
            instance_r_check = \
                (prop == "instance_r" and winattr == win.window_instance)
            role_r_check = \
                (prop == "role_r" and winattr == win.window_role)
            if class_r_check or instance_r_check or role_r_check:
                # self.cfg[target_tag][prop].remove(target_tag)
                pass

        lst_by_reg = []
        # Delete appropriate regexes
        for prop in self.cfg[target_tag].copy():
            if prop in self.cfg_regex_props():
                for reg in self.cfg[target_tag][prop].copy():
                    if prop == "class_r":
                        lst_by_reg = self.i3ipc.get_tree().find_classed(reg)
                    if prop == "instance_r":
                        lst_by_reg = self.i3ipc.get_tree().find_instanced(reg)
                    if prop == "role_r":
                        lst_by_reg = self.i3ipc.get_tree().find_by_role(reg)
                    winattr = self.win_attrs[prop[:-2]]
                    for win in lst_by_reg:
                        check_for_win_attrs(win, prop)

    def del_props(self, tag: str, prop_str: str) -> None:
        """ Remove window from some tag.
        tag (str): target tag
        prop_str (str): property string in special format. """
        self.property_to_winattrib(prop_str)
        self.del_direct_props(tag)
        self.del_regex_props(tag)
        # Cleanup
        for prop in self.cfg_regex_props() | self.cfg_props():
            if prop in self.conf(tag) and self.conf(tag, prop) == set():
                del self.cfg[tag][prop]
