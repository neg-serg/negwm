""" Dynamic TOML-based config for negi3mods.

This is a superclass for negi3mods which want to store configuration via TOML
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import re
import os
import sys
from typing import Set, Callable
import toml
import traceback
from main import Misc


class modi3cfg(object):
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

        self.i3 = i3
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

    def extract_prog_str(self, conf_part: str,
                         prog_field: str = "prog", exe_file: bool = True):
        """ Helper to extract prog(by default) string from config

        Args:
            conf_part (str): part of config from where you want to extract it.
            prog_field (str): string name to extract.
        """
        if conf_part is None:
            return

        if exe_file:
            return re.sub(
                "~",
                os.path.realpath(os.path.expandvars("$HOME")),
                conf_part.get(prog_field, "")
            )
        else:
            return conf_part.get(prog_field, "")

    def cfg_regex_props(self) -> Set[str]:
        # regex cfg properties
        return {"class_r", "instance_r", "name_r", "role_r"}

    def win_all_props(self):
        # basic + regex props
        return self.cfg_props() | self.cfg_regex_props()

    def possible_props(self) -> Set[str]:
        # windows properties used for props add / del
        return {'class', 'instance', 'window_role', 'title'}

    def cfg_props(self) -> Set[str]:
        # basic cfg properties, without regexes
        return {'class', 'instance', 'name', 'role'}

    def subtag_attr_list(self) -> Set[str]:
        return self.possible_props()

    def reload_config(self, *arg) -> None:
        """ Reload config for current selected module.
            Call load_config, print debug messages and reinit all stuff.
        """
        prev_conf = self.cfg
        try:
            self.load_config()
            if self.loop is None:
                self.__init__(self.i3)
            else:
                self.__init__(self.i3, loop=self.loop)
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
        self.dict_apply(lambda key: list(key), self.deconvert_subtag)

    def convert_subtag(self, subtag: str) -> None:
        """ Convert subtag attributes to set for the better performance.

            Args:
                subtag (str): target subtag.
        """
        self.subtag_apply(subtag, lambda key: set(key))

    def deconvert_subtag(self, subtag: str) -> None:
        """ Convert set attributes to list, because of set cannot be saved
        / restored to / from TOML-files corretly.

            Args:
                subtag (str): target subtag.
        """
        self.subtag_apply(subtag, lambda key: list(key))

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

    def subtag_apply(self, subtag: str, field_conv: Callable) -> None:
        """ Convert subtag attributes to set for the better performance.

            Args:
                subtag (str): target subtag name.
                field_conv (Callable): function to convert dict field.
        """
        for val in subtag.values():
            for key in val:
                if key in self.subtag_attr_list():
                    val[sys.intern(key)] = field_conv(val[sys.intern(key)])

    def load_config(self) -> None:
        """ Reload config itself and convert lists in it to sets for the better
            performance.
        """
        with open(self.i3_cfg_mod_path, "r") as fp:
            self.cfg = toml.load(fp)
        if self.convert_me:
            self.dict_converse()

    def dump_config(self) -> None:
        """ Dump current config, can be used for debugging.
        """
        with open(self.i3_cfg_mod_path, "r+") as fp:
            if self.convert_me:
                self.dict_deconverse()
            toml.dump(self.cfg, fp)
            self.cfg = toml.load(fp)
        if self.convert_me:
            self.dict_converse()

    def property_to_winattrib(self, prop_str: str) -> None:
        """ Parse property string to create win_attrs dict.
            Args:
                prop_str (str): property string in special format.
        """
        self.win_attrs = {}
        prop_str = prop_str[1:-1]
        for t in prop_str.split('@'):
            if len(t):
                toks = t.split('=')
                attr = toks[0]
                value = toks[1]
                if value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                if attr in self.subtag_attr_list():
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
            for t in ftors:
                if self.win_attrs[t] not in self.cfg.get(tag, {}).get(t, {}):
                    if t in self.cfg[tag]:
                        if type(self.cfg[tag][t]) == str:
                            self.cfg[tag][t] = {self.win_attrs[t]}
                        elif type(self.cfg[tag][t]) == set:
                            self.cfg[tag][t].add(self.win_attrs[t])
                    else:
                        self.cfg[tag].update({t: self.win_attrs[t]})
                    # special fix for the case where attr
                    # is just attr not {attr}
                    if type(self.conf(tag, t)) == str:
                        self.cfg[tag][t] = {self.win_attrs[t]}

    def del_direct_props(self, tag: str) -> None:
        """ Remove basic(non-regex) properties of window from target tag.
            Args:
                tag (str): target tag
        """
        # Delete 'direct' props:
        for t in self.cfg[tag].copy():
            if t in self.cfg_props():
                if type(self.conf(tag, t)) is str:
                    del self.cfg[tag][t]
                elif type(self.conf(tag, t)) is set:
                    for tok in self.cfg[tag][t].copy():
                        if self.win_attrs[t] == tok:
                            self.cfg[tag][t].remove(tok)

    def del_regex_props(self, tag: str) -> None:
        """ Remove regex properties of window from target tag.
            Args:
                tag (str): target tag
        """
        # Delete appropriate regexes
        for t in self.cfg[tag].copy():
            if t in self.cfg_regex_props():
                for reg in self.cfg[tag][t].copy():
                    if t == "class_r":
                        lst_by_reg = self.i3.get_tree().find_classed(reg)
                    if t == "instance_r":
                        lst_by_reg = self.i3.get_tree().find_instanced(reg)
                    if t == "role_r":
                        lst_by_reg = self.i3.get_tree().find_by_role(reg)
                    for l in lst_by_reg:
                        if (t == "class_r" and self.win_attrs[t[:-2]] == l.window_class) \
                            or (t == "instance_r" and self.win_attrs[t[:-2]] == l.window_instance) \
                                or (t == "role_r" and self.win_attrs[t[:-2]] == l.window_role):
                                    self.cfg[tag][t].remove(reg)

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
        for t in self.cfg_regex_props() | self.cfg_props():
            if t in self.conf(tag) and self.conf(tag, t) == set():
                del self.cfg[tag][t]

