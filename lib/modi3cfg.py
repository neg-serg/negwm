""" Dynamic TOML-based config for negi3mods.

This is a superclass for negi3mods which want to store configuration via TOML
files. It supports inotify-based updating of self.cfg dynamically and has
pretty simple API. I've considered that inheritance here is good idea.
"""

import sys
import toml
import traceback
from modlib import i3path


class modi3cfg(object):
    def __init__(self, i3, loop=None):
        # detect current negi3mod
        self.mod = self.__class__.__name__

        # negi3mod cfg directory path
        self.i3_cfg_mod_path = i3path() + '/cfg/' + self.mod + '.cfg'

        # load current config
        self.load_config()

        # used for props add / del hacks
        self.win_attrs = {}

        # windows properties used for props add / del
        self.possible_props = ['class', 'instance', 'window_role', 'title']

        # basic cfg properties, without regexes
        self.cfg_props = ['class', 'instance', 'role']

        # regex cfg properties
        self.cfg_regex_props = ["class_r", "instance_r", "name_r", "role_r"]

        # basic + regex props
        self.win_all_props = set(self.cfg_props) | set(self.cfg_regex_props)

        # bind numbers to cfg names
        self.conv_props = {
            'class': self.cfg_props[0],
            'instance': self.cfg_props[1],
            'window_role': self.cfg_props[2],
        }

        self.i3 = i3
        self.loop = None
        if loop is not None:
            self.loop = loop

    def reload_config(self):
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
        except:
            print(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__()

    def dict_converse(self):
        """ Convert list attributes to set for the better performance.
        """
        for i in self.cfg:
            if type(i) is list:
                for j in self.cfg[i]:
                    if j in self.win_all_props:
                        self.cfg[i][j] = set(self.cfg[i][sys.intern(j)])
                    if j == "prog_dict":
                        for k in self.cfg[i][j]:
                            for kk in self.cfg[i][j][k]:
                                if kk == "includes":
                                    self.cfg[i][j][k][kk] = \
                                        set(self.cfg[i][j][k][sys.intern(kk)])

    def dict_deconverse(self):
        """ Convert set attributes to list, because of set cannot be saved
            / restored to / from TOML-files corretly.
        """
        for i in self.cfg:
            if type(i) is dict:
                for j in self.cfg[i]:
                    if j in self.win_all_props:
                        self.cfg[i][j] = list(self.cfg[i][j])
                    if j == "prog_dict":
                        for k in self.cfg[i][j]:
                            for kk in self.cfg[i][j][k]:
                                if kk == "includes":
                                    self.cfg[i][j][k][kk] = \
                                        list(self.cfg[i][j][k][kk])

    def load_config(self):
        """ Reload config itself and convert lists in it to sets for the better
            performance.
        """
        with open(self.i3_cfg_mod_path, "r") as fp:
            self.cfg = toml.load(fp)
        self.dict_converse()

    def dump_config(self):
        """ Dump current config, can be used for debugging.
        """
        with open(self.i3_cfg_mod_path, "r+") as fp:
            self.dict_deconverse()
            toml.dump(self.cfg, fp)
            self.cfg = toml.load(fp)
        self.dict_converse()

    def property_to_winattrib(self, prop_str):
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
                if attr in self.possible_props:
                    self.win_attrs[self.conv_props.get(attr, {})] = value

    def add_props(self, tag, prop_str):
        """ Move window to some tag.
            Args:
                tag (str): target tag
                prop_str (str): property string in special format.
        """
        self.property_to_winattrib(prop_str)
        ftors = set(self.cfg_props) & set(self.win_attrs.keys())
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
                    if type(self.cfg[tag][t]) == str:
                        self.cfg[tag][t] = {self.win_attrs[t]}

    def del_props(self, tag, prop_str):
        """ Remove window from some tag.
            Args:
                tag (str): target tag
                prop_str (str): property string in special format.
        """
        self.property_to_winattrib(prop_str)
        # Delete 'direct' props:
        for t in self.cfg[tag].copy():
            if t in self.cfg_props:
                if type(self.cfg[tag][t]) is str:
                    del self.cfg[tag][t]
                elif type(self.cfg[tag][t]) is set:
                    for tok in self.cfg[tag][t].copy():
                        if self.win_attrs[t] == tok:
                            self.cfg[tag][t].remove(tok)
        # Delete appropriate regexes
        for t in self.cfg[tag].copy():
            if t in self.cfg_regex_props:
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

        # Cleanup
        for t in set(self.cfg_regex_props) | set(self.cfg_props):
            if t in self.cfg[tag] and self.cfg[tag][t] == set():
                del self.cfg[tag][t]

