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
        self.mod = self.__class__.__name__
        self.i3_path = i3path()
        self.load_config()
        self.attr_dict = {}
        self.possible_props = ['class', 'instance', 'window_role', 'title']
        self.cfg_props = ['class', 'instance', 'role']
        self.cfg_regex_props = ["class_r", "instance_r", "name_r", "role_r"]
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
        for i in self.cfg:
            if type(i) is list:
                for j in self.cfg[i]:
                    if j in {"class", "class_r", "instance"}:
                        self.cfg[i][j] = set(self.cfg[i][sys.intern(j)])
                    if j == "prog_dict":
                        for k in self.cfg[i][j]:
                            for kk in self.cfg[i][j][k]:
                                if kk == "includes":
                                    self.cfg[i][j][k][kk] = \
                                        set(self.cfg[i][j][k][sys.intern(kk)])

    def dict_deconverse(self):
        for i in self.cfg:
            if type(i) is dict:
                for j in self.cfg[i]:
                    if j in {"class", "class_r", "instance"}:
                        self.cfg[i][j] = list(self.cfg[i][j])
                    if j == "prog_dict":
                        for k in self.cfg[i][j]:
                            for kk in self.cfg[i][j][k]:
                                if kk == "includes":
                                    self.cfg[i][j][k][kk] = \
                                        list(self.cfg[i][j][k][kk])

    def load_config(self):
        with open(self.i3_path + "/cfg/" + self.mod + ".cfg", "r") as fp:
            self.cfg = toml.load(fp)
        self.dict_converse()

    def dump_config(self):
        with open(self.i3_path + "/cfg/" + self.mod + ".cfg", "r+") as fp:
            self.dict_deconverse()
            toml.dump(self.cfg, fp)
            self.cfg = toml.load(fp)
        self.dict_converse()

    def fill_attr_dict(self, prop_str):
        self.attr_dict = {}
        prop_str = prop_str[1:-1]
        for t in prop_str.split('@'):
            if len(t):
                toks = t.split('=')
                attr = toks[0]
                value = toks[1]
                if value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                if attr in self.possible_props:
                    self.attr_dict[self.conv_props.get(attr, {})] = value

    def get_prev_tag(self, prop_str):
        self.fill_attr_dict(prop_str)
        for tag in self.cfg:
            for t in self.cfg[tag]:
                # Look by ordinary props
                if t in self.cfg_props:
                    for val in self.cfg[tag][t]:
                        if t == 'class':
                            if self.attr_dict['class'] == val:
                                return tag
                        if t == 'instance':
                            if self.attr_dict['instance'] == val:
                                return tag
                        if t == 'role':
                            if self.attr_dict['role'] == val:
                                return tag
                # Look for regex props
                if t in self.cfg_regex_props:
                    if t == "class_r":
                        for reg in self.cfg[tag][t]:
                            lst_by_reg = self.i3.get_tree().find_classed(reg)
                            for l in lst_by_reg:
                                if self.attr_dict[t[:-2]] == l.window_class \
                                        or self.attr_dict[t[:-2]] == l.window_instance:
                                    return tag
                    if t == "role_r":
                        for reg in self.cfg[tag][t]:
                            lst_by_reg = self.i3.get_tree().find_by_role(reg)
                            for l in lst_by_reg:
                                if self.attr_dict[t[:-2]] == l.window_role:
                                    return tag

    def add_props(self, tag, prop_str):
        self.fill_attr_dict(prop_str)
        ftors = set(self.cfg_props) & set(self.attr_dict.keys())
        if tag in self.cfg:
            for t in ftors:
                if self.attr_dict[t] not in self.cfg.get(tag, {}).get(t, {}):
                    if t in self.cfg[tag]:
                        if type(self.cfg[tag][t]) == str:
                            self.cfg[tag][t] = {self.attr_dict[t]}
                        elif type(self.cfg[tag][t]) == set:
                            self.cfg[tag][t].add(self.attr_dict[t])
                    else:
                        self.cfg[tag].update({t: self.attr_dict[t]})
                    # special fix for the case where attr
                    # is just attr not {attr}
                    if type(self.cfg[tag][t]) == str:
                        self.cfg[tag][t] = {self.attr_dict[t]}

    def del_props(self, tag, prop_str):
        self.fill_attr_dict(prop_str)
        # Delete 'direct' props:
        for t in self.cfg[tag].copy():
            if t in self.cfg_props:
                if type(self.cfg[tag][t]) is str:
                    del self.cfg[tag][t]
                elif type(self.cfg[tag][t]) is set:
                    for tok in self.cfg[tag][t].copy():
                        if self.attr_dict[t] == tok:
                            self.cfg[tag][t].remove(tok)
        # Delete appropriate regexes
        for t in self.cfg[tag].copy():
            if t in self.cfg_regex_props:
                if t == "class_r":
                    for reg in self.cfg[tag][t].copy():
                        lst_by_reg = self.i3.get_tree().find_classed(reg)
                        for l in lst_by_reg:
                            if self.attr_dict[t[:-2]] == l.window_class:
                                self.cfg[tag][t].remove(reg)
                if t == "instance_r":
                    for reg in self.cfg[tag][t].copy():
                        lst_by_reg = self.i3.get_tree().find_classed(reg)
                        for l in lst_by_reg:
                            if self.attr_dict[t[:-2]] == l.window_instance:
                                self.cfg[tag][t].remove(reg)
                if t == "role_r":
                    for reg in self.cfg[tag][t].copy():
                        lst_by_reg = self.i3.get_tree().find_by_role(reg)
                        for l in lst_by_reg:
                            if self.attr_dict[t[:-2]] == l.window_role:
                                self.cfg[tag][t].remove(reg)

        # Cleanup
        for t in set(self.cfg_regex_props) | set(self.cfg_props):
            if t in self.cfg[tag] and self.cfg[tag][t] == set():
                del self.cfg[tag][t]

