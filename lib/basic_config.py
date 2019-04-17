""" Dynamic TOML-based config for basic negi3mods.

It is the simplified version of modi3cfg for modules like polybar_vol, etc.
There are no external dependecies like i3 or asyncio.

"""

import sys
import toml
import traceback
import asyncio
import aionotify
from misc import Misc


class modconfig(object):
    def __init__(self, loop):
        # set asyncio loop
        self.loop = loop

        # detect current negi3mod
        self.mod = self.__class__.__name__

        # config dir path
        self.i3_cfg_path = Misc.i3path() + '/cfg/'

        # negi3mod config path
        self.mod_cfg_path = self.i3_cfg_path + self.mod + '.cfg'

        # load current config
        self.load_config()

        # run inotify watcher to update config on change.
        self.run_inotify_watchers()

    def reload_config(self):
        """ Reload config.
            Call load_config and reinit all stuff.
        """
        prev_conf = self.cfg
        try:
            self.load_config()
            self.__init__()
            self.special_reload()
        except Exception:
            traceback.print_exc(file=sys.stdout)
            self.cfg = prev_conf
            self.__init__()

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

    def cfg_watcher(self):
        """ modi3cfg watcher to update modules config in realtime.
        """
        watcher = aionotify.Watcher()
        watcher.watch(alias='cfg', path=self.i3_cfg_path,
                      flags=aionotify.Flags.MODIFY)
        return watcher

    async def cfg_worker(self, watcher):
        """ Reload target config

            Args:
                watcher: watcher for cfg.
        """
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            if event.name == self.mod + '.cfg':
                self.reload_config()
                Misc.notify_msg(f'[Reloaded {self.mod} ]')
        watcher.close()

    def run_inotify_watchers(self):
        """ Start all watchers here via ensure_future to run it in background.
        """
        asyncio.ensure_future(self.cfg_worker(self.cfg_watcher()))

