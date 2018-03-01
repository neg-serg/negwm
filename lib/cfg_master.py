import os
import sys
import toml
import traceback
import i3ipc


class CfgMaster(object):
    def __init__(self):
        self.mod = self.__class__.__name__
        self.load_config()
        self.attr_dict = {}
        self.possible_props = ['class', 'instance', 'window_role', 'title']
        self.cfg_props = [ 'class', 'instance', 'role' ]
        self.cfg_regex_props = [ "class_r", "instance_r", "name_r", "role_r" ]
        self.conv_props = {
            'class': self.cfg_props[0],
            'instance': self.cfg_props[1],
            'window_role': self.cfg_props[2],
        }
        self.i3 = i3ipc.Connection()

    def reload_config(self):
        prev_conf = self.cfg
        try:
            self.load_config()
            self.__init__()
            print(f"[{self.mod}] config reloaded")
        except:
            print(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__()

    def dict_converse(self):
        for i in self.cfg:
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
        user_name = os.environ.get("USER", "neg")
        xdg_config_path = os.environ.get("XDG_CONFIG_HOME", "/home/" +
                                         user_name + "/.config/")
        self.i3_path = xdg_config_path+"/i3/"
        with open(self.i3_path + "/cfg/" + self.mod + ".cfg", "r") as fp:
            self.cfg = toml.load(fp)
        self.dict_converse()

    def dump_config(self):
        user_name = os.environ.get("USER", "neg")
        xdg_config_path = os.environ.get("XDG_CONFIG_HOME", "/home/" +
                                         user_name + "/.config/")
        self.i3_path = xdg_config_path+"/i3/"
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
                    val = self.attr_dict.get(t, {})
                    if val:
                        if val in self.cfg[tag][t]:
                            return tag
                if t in self.cfg_regex_props:
                    if t == "class_r":
                        for reg in self.cfg[tag][t].copy():
                            lst_by_reg = self.i3.get_tree().find_classed(reg)
                            for l in lst_by_reg:
                                if self.attr_dict[t[:-2]] == l.window_class:
                                    return tag
                    if t == "role_r":
                        for reg in self.cfg[tag][t].copy():
                            lst_by_reg = self.i3.get_tree().find_by_role(reg)
                            for l in lst_by_reg:
                                if self.attr_dict[t[:-2]] == l.window_role:
                                    return tag

    def add_props(self, tag, prop_str):
        self.fill_attr_dict(prop_str)
        for t in self.cfg[tag]:
            if t in self.cfg_props:
                if self.attr_dict[t] not in self.cfg[tag][t]:
                    self.cfg[tag][t].add(self.attr_dict[t])

    def del_props(self, tag, prop_str):
        self.fill_attr_dict(prop_str)
        # Delete 'direct' props:
        print(f'tag={tag}')
        for t in self.cfg[tag]:
            if t in self.cfg_props:
                if self.attr_dict[t] in self.cfg[tag][t]:
                    self.cfg[tag][t].remove(self.attr_dict[t])

        # Delete appropriate regexes
        for t in self.cfg[tag]:
            if t in self.cfg_regex_props:
                if t == "class_r":
                    for reg in self.cfg[tag][t].copy():
                        lst_by_reg = self.i3.get_tree().find_classed(reg)
                        for l in lst_by_reg:
                            if self.attr_dict[t[:-2]] == l.window_class:
                                try:
                                    self.cfg[tag][t].remove(reg)
                                except KeyError:
                                    pass
                                break
                if t == "role_r":
                    for reg in self.cfg[tag][t].copy():
                        lst_by_reg = self.i3.get_tree().find_by_role(reg)
                        for l in lst_by_reg:
                            if self.attr_dict[t[:-2]] == l.window_role:
                                try:
                                    self.cfg[tag][t].remove(reg)
                                except KeyError:
                                    pass
                                break

