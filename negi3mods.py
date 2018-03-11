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
        self.loop = asyncio.get_event_loop()

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
        self.manager = daemon_manager(self.mods)
        for mod in self.mods.keys():
            i3mod = importlib.import_module(mod + "d")
            self.mods[mod] = getattr(i3mod, mod)(self.i3)
            self.manager.add_daemon(mod)

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

    def run_inotify_watchers(self):
        asyncio.ensure_future(self.mods_cfg_worker(self.mods_cfg_watcher()))
        asyncio.ensure_future(self.i3_config_worker(self.i3_config_watcher()))

    def main(self):
        def start(func, name, args=None):
            print(f'[{name} loading ', end='')
            if args is None:
                func()
            elif args is not None:
                func(*args)
            print(f'... {name} loaded]')

        use_inotify = True
        start(self.load_modules, 'modules')
        if use_inotify:
            start(self.run_inotify_watchers, 'inotify watchers')

        threads = {
            'mainloop': Thread(target=self.manager.mainloop, args=(self.loop,), daemon=True),
            'info': Thread(target=self.mods["info"].listen, daemon=True),
        }

        start(threads['mainloop'].start, 'mainloop')
        start(threads['info'].start, 'info')

        for t in threads:
            # join with timeout. Without timeout signal cannot be caught.
            threads[t].join(0.1)
            print(f'>>joined {threads[t]}')
        print('... everything loaded ...')
        try:
            start(self.i3.main, 'i3.main()')
        except KeyboardInterrupt:
            self.i3.main_quit()
        print('... exit ...')


if __name__ == '__main__':
    get_lock('negi3mods.py')
    cgitb.enable(format='text')

    atexit.register(lambda: os._exit(0))

    daemon = Negi3Mods()
    daemon.main()

