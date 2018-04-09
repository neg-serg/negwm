""" Dynamic TOML-based config for basic negi3mods.

It is the simplified version of modi3cfg for modules like vol_printer, etc.
There are no external dependecies like i3 or asyncio.

"""

import sys
import toml
import traceback
from modlib import i3path


class modconfig(object):
    def __init__(self):
        # detect current negi3mod
        self.mod = self.__class__.__name__

        # negi3mod config path
        self.mod_cfg_path = i3path() + '/cfg/' + self.mod + '.cfg'

        # load current config
        self.load_config()

    def reload_config(self):
        """ Reload config for current selected module.
            Call load_config, print debug messages and reinit all stuff.
        """
        prev_conf = self.cfg
        try:
            self.load_config()
            self.__init__(self.i3)
            print(f"[{self.mod}] config reloaded")
        except:
            print(f"[{self.mod}] config reload failed")
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__()

    def load_config(self):
        """ Reload config itself and convert lists in it to sets for the better
            performance.
        """
        with open(self.mod_cfg_path, "r") as fp:
            self.cfg = toml.load(fp)

    def dump_config(self):
        """ Dump current config, can be used for debugging.
        """
        with open(self.mod_cfg_path, "r+") as fp:
            toml.dump(self.cfg, fp)
            self.cfg = toml.load(fp)

