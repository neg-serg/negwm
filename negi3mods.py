#!/usr/bin/pypy3
""" i3 negi3mods daemon script Usage:
    negi3mods.py

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2018

"""

import os
import sys
import socket
import importlib
import atexit
import subprocess
import shlex
import cgitb
import asyncio
import aionotify
import i3ipc
from threading import Thread
from lib.modlib import daemon_manager

# Create a pid lock with abstract socket.
# Taken from [https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running]
def get_lock(process_name):
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + process_name)
        print('locking successful')
    except socket.error:
        print('lock exists')
        sys.exit()


class Negi3Mods():
    def __init__(self):
        self.mods = {
            sys.intern('circle'): None,
            sys.intern('ns'): None,
            sys.intern('flast'): None,
            sys.intern('menu'): None,
            sys.intern('fsdpms'): None,
            sys.intern('info'): None,
            sys.intern('wm3'): None,
            sys.intern('vol'): None,
        }
        user_name = os.environ.get("USER", "neg")
        xdg_config_path = os.environ.get(
            "XDG_CONFIG_HOME", "/home/" + user_name + "/.config/"
        )
        self.i3_path = xdg_config_path + "/i3/"
        self.i3 = i3ipc.Connection()

    def dump_configs(self):
        import toml
        try:
            for mod in self.mods.keys():
                m = self.mods[mod]
                with open(self.i3_path + "/cfg/" + mod + ".cfg", "w") as fp:
                    toml.dump(m.cfg, fp)
        except:
            pass

    def load_modules(self):
        manager = daemon_manager(self.mods)
        for mod in self.mods.keys():
            i3mod = importlib.import_module(mod + "d")
            self.mods[mod] = getattr(i3mod, mod)(self.i3)
            manager.add_daemon(mod)
        Thread(target=self.mods["info"].listen, daemon=True).start()
        Thread(target=self.i3.main, daemon=True).start()
        manager.mainloop()

    def cleanup_on_exit(self):
        def cleanup_everything():
            for mod in self.mods.keys():
                fifo = self.mods[mod]["manager"].daemons[mod].fifos[mod]
                if os.path.exists(fifo):
                    os.remove(fifo)
        atexit.register(cleanup_everything)

    def mods_cfg_watcher(self):
        watcher = aionotify.Watcher()
        watcher.watch(
            alias='configs',
            path=self.i3_path + "/cfg/",
            flags=aionotify.Flags.MODIFY,
        )
        return watcher

    def i3_config_watcher(self):
        watcher = aionotify.Watcher()
        watcher.watch(
            alias='i3cfg',
            path=self.i3_path,
            flags=aionotify.Flags.CLOSE_WRITE,
        )
        return watcher

    async def mods_cfg_worker(self, watcher):
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            if event.name[:-4] in self.mods:
                for mod in self.mods.keys():
                    subprocess.Popen(shlex.split(self.i3_path + "send " + mod + " reload"))
        watcher.close()

    async def i3_config_worker(self, watcher):
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            if event.name == '_config':
                with open(self.i3_path + "/config", "w") as fp:
                    subprocess.run(
                        shlex.split("ppi3 " + self.i3_path + "_config"),
                        stdout=fp
                    )
        watcher.close()

    def check_i3_config(self):
        check_config = subprocess.run(
            ['i3', '-C'],
            stdout=subprocess.PIPE
        ).stdout.decode('utf-8')
        if len(check_config):
            subprocess.Popen(
                shlex.split(
                    f"notify-send '{check_config.encode('utf-8')}'"
                )
            )
        check_config = ""

    def start_inotify_watchers(self):
        # Prepare the loop
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(
            asyncio.wait([
                self.mods_cfg_worker(self.mods_cfg_watcher()),
                self.i3_config_worker(self.i3_config_watcher())
            ])
        )
        print('[i3 cfg watcher enabled]')
        self.loop.stop()
        self.loop.close()

    def main(self):
        use_inotify = True
        print("[starting modules loading]")
        self.load_modules()
        print("[modules loaded]")
        self.i3.main()
        if use_inotify:
            print("[starting inotify]")
            self.start_inotify_watchers()
            print("[inotify started]")

if __name__ == '__main__':
    get_lock('negi3mods.py')
    cgitb.enable(format='text')
    daemon = Negi3Mods()
    daemon.main()

