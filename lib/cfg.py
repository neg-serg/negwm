""" Dynamic TOML-based config for negi3mods.

This is a superclass for negi3mods which want to store configuration via TOML
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import re
import os
import sys
from typing import Set, Callable
import traceback

import toml
from misc import Misc


class cfg(object):
    def __init__(self, i3, convert_me: bool = False, loop=None) -> None:
        # detect current negi3mod
        self.mod = self.__class__.__name__

        # negi3mod config path
        self.i3_cfg_mod_path = Misc.i3path() + '/cfg/' + self.mod + '.cfg'

        # convert config values or not
        self.convert_me = convert_me

        # load current config
        self.load_config()

        # used for props add / del hacks
        self.win_attrs = {}

        # bind numbers to cfg names
        self.conv_props = {
            'class': 'class',
            'instance': 'instance',
            'window_role': 'window_role',
            'title': 'name',
        }

        self.i3ipc = i3
        self.loop = None
        if loop is not None:
            self.loop = loop

    def conf(self, *conf_path):
        """ Helper to extract config for current tag.

        Args:
            conf_path: path of config from where extract.
        """
        ret = {}
        for part in conf_path:
            if not ret:
                ret = self.cfg.get(part)
            else:
                ret = ret.get(part)
        return ret

    @staticmethod
    def extract_prog_str(conf_part: str,
                         prog_field: str = "prog", exe_file: bool = True):
        """ Helper to extract prog(by default) string from config

        Args:
            conf_part (str): part of config from where you want to extract it.
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
        # regex cfg properties
        return {"class_r", "instance_r", "name_r", "role_r"}

    def win_all_props(self):
        """ All window props """
        # basic + regex props
        return self.cfg_props() | self.cfg_regex_props()

    @staticmethod
    def possible_props() -> Set[str]:
        """ Possible window props """
        # windows properties used for props add / del
        return {'class', 'instance', 'window_role', 'title'}

    @staticmethod
    def cfg_props() -> Set[str]:
        """ basic window props """
        # basic cfg properties, without regexes
        return {'class', 'instance', 'name', 'role'}

    @staticmethod
    def subtag_attr_list() -> Set[str]:
        """ Helper to create subtag attr list. """
        return cfg.possible_props()

    def reload_config(self, *arg) -> None:
        """ Reload config for current selected module.
            Call load_config, print debug messages and reinit all stuff.
        """
        prev_conf = self.cfg
        try:
            self.load_config()
            if self.loop is None:
                self.__init__(self.i3ipc)
            else:
                self.__init__(self.i3ipc, loop=self.loop)
            print(f"[{self.mod}] config reloaded")
        except Exception:
            print(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__()

    def dict_converse(self) -> None:
        """ Convert list attributes to set for the better performance.
        """
        self.dict_apply(lambda key: set(key), self.convert_subtag)

    def dict_deconverse(self) -> None:
        """ Convert set attributes to list, because of set cannot be saved
            / restored to / from TOML-files corretly.
        """
        self.dict_apply(lambda key: list(key), cfg.deconvert_subtag)

    def convert_subtag(subtag: str) -> None:
        """ Convert subtag attributes to set for the better performance.

            Args:
                subtag (str): target subtag.
        """
        cfg.subtag_apply(subtag, lambda key: set(key))

    @staticmethod
    def deconvert_subtag(self, subtag: str) -> None:
        """ Convert set attributes to list, because of set cannot be saved
        / restored to / from TOML-files corretly.

            Args:
                subtag (str): target subtag.
        """
        cfg.subtag_apply(subtag, lambda key: list(key))

    def dict_apply(self, field_conv: Callable, subtag_conv: Callable) -> None:
        """ Convert list attributes to set for the better performance.

            Args:
                field_conv (Callable): function to convert dict field.
                subtag_conv (Callable): function to convert subtag inside dict.
        """
        for string in self.cfg.values():
            for key in string:
                if key in self.win_all_props():
                    string[sys.intern(key)] = field_conv(
                        string[sys.intern(key)]
                    )
                elif key == "subtag":
                    subtag_conv(string[sys.intern(key)])

    @staticmethod
    def subtag_apply(subtag: str, field_conv: Callable) -> None:
        """ Convert subtag attributes to set for the better performance.

            Args:
                subtag (str): target subtag name.
                field_conv (Callable): function to convert dict field.
        """
        for val in subtag.values():
            for key in val:
                if key in cfg.subtag_attr_list():
                    val[sys.intern(key)] = field_conv(val[sys.intern(key)])

    def load_config(self) -> None:
        """ Reload config itself and convert lists in it to sets for the better
            performance.
        """
        with open(self.i3_cfg_mod_path, "r") as negi3modcfg:
            self.cfg = toml.load(negi3modcfg)
        if self.convert_me:
            self.dict_converse()

    def dump_config(self) -> None:
        """ Dump current config, can be used for debugging.
        """
        with open(self.i3_cfg_mod_path, "r+") as negi3modcfg:
            if self.convert_me:
                self.dict_deconverse()
            toml.dump(self.cfg, negi3modcfg)
            self.cfg = toml.load(negi3modcfg)
        if self.convert_me:
            self.dict_converse()

    def property_to_winattrib(self, prop_str: str) -> None:
        """ Parse property string to create win_attrs dict.
            Args:
                prop_str (str): property string in special format.
        """
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
            Args:
                tag (str): target tag
                prop_str (str): property string in special format.
        """
        self.property_to_winattrib(prop_str)
        ftors = self.cfg_props() & set(self.win_attrs.keys())
        if tag in self.cfg:
            for tok in ftors:
                if self.win_attrs[tok] not in self.cfg.get(tag, {}).get(tok, {}):
                    if tok in self.cfg[tag]:
                        if isinstance(self.cfg[tag][tok], str):
                            self.cfg[tag][tok] = {self.win_attrs[tok]}
                        elif isinstance(self.cfg[tag][tok], set):
                            self.cfg[tag][tok].add(self.win_attrs[tok])
                    else:
                        self.cfg[tag].update({tok: self.win_attrs[tok]})
                    # special fix for the case where attr
                    # is just attr not {attr}
                    if isinstance(self.conf(tag, tok), str):
                        self.cfg[tag][tok] = {self.win_attrs[tok]}

    def del_direct_props(self, target_tag: str) -> None:
        """ Remove basic(non-regex) properties of window from target tag.
            Args:
                tag (str): target tag
        """
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
            Args:
                target_tag (str): target tag
        """
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
                    for l in lst_by_reg:
                        class_r_check = (prop == "class_r" and winattr == l.window_class)
                        instance_r_check = (prop == "instance_r" and winattr == l.window_instance)
                        role_r_check = (prop == "role_r" and winattr == l.window_role)
                        if class_r_check or instance_r_check or role_r_check:
                            self.cfg[target_tag][prop].remove(target_tag)

    def del_props(self, tag: str, prop_str: str) -> None:
        """ Remove window from some tag.
            Args:
                tag (str): target tag
                prop_str (str): property string in special format.
        """
        self.property_to_winattrib(prop_str)
        self.del_direct_props(tag)
        self.del_regex_props(tag)

        # Cleanup
        for prop in self.cfg_regex_props() | self.cfg_props():
            if prop in self.conf(tag) and self.conf(tag, prop) == set():
                del self.cfg[tag][prop]

