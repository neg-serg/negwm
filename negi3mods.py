#!/usr/bin/pypy3
""" i3 negi3mods daemon script Usage:
    negi3mods.py

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2018 """

import os
import timeit
from sys import intern
import subprocess
import importlib
import atexit
import cgitb
import asyncio
import aionotify
import i3ipc
from threading import Thread
from lib.locker import get_lock
from lib.modlib import daemon_manager, notify_msg, i3path


class Negi3Mods():
    def __init__(self):
        self.mods = {
            intern('circle'): None,
            intern('ns'): None,
            intern('flast'): None,
            intern('menu'): None,
            intern('fsdpms'): None,
            intern('wm3'): None,
            intern('vol'): None,
        }
        self.notification_text = "Wow! It's time to start mods!\n\n"
        self.msg_prefix = "<span weight='normal' color='#395573'> >> </span>"
        self.i3_path = i3path()
        self.i3_cfg_path = self.i3_path + '/cfg/'
        self.i3 = i3ipc.Connection()
        self.loop = asyncio.get_event_loop()

    def dump_configs(self):
        import toml
        try:
            for mod in self.mods.keys():
                m = self.mods[mod]
                with open(self.i3_cfg_path + mod + ".cfg", "w") as fp:
                    toml.dump(m.cfg, fp)
        except:
            pass

    def load_modules(self):
        mod_startup_times = []
        self.manager = daemon_manager(self.mods)
        print()
        for mod in self.mods.keys():
            start_time = timeit.default_timer()
            i3mod = importlib.import_module(mod + "d")
            self.mods[mod] = getattr(i3mod, mod)(self.i3, loop=self.loop)
            self.manager.add_daemon(mod)
            mod_startup_times.append(timeit.default_timer() - start_time)
            time_elapsed = f'{mod_startup_times[-1]:4f}s'
            mod_text = f'[{mod}]'
            mod_loaded_info = f'Loaded {mod_text:<10s} ~ {time_elapsed:>10s}'
            self.notification_text += self.msg_prefix + mod_loaded_info + '\n'
            print(mod_loaded_info, flush=True)
        overall_msg = f'Overall time = {sum(mod_startup_times):6f}s'
        self.notification_text += overall_msg
        print(overall_msg)

    def cleanup_on_exit(self):
        def cleanup_everything():
            for mod in self.mods.keys():
                fifo = self.mods[mod]["manager"].daemons[mod].fifos[mod]
                if os.path.exists(fifo):
                    os.remove(fifo)
        atexit.register(cleanup_everything)

    def mods_cfg_watcher(self):
        watcher = aionotify.Watcher()
        watcher.watch(alias='configs', path=self.i3_cfg_path,
                      flags=aionotify.Flags.MODIFY)
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
                    subprocess.run([self.i3_path + 'send', mod, 'reload'])
        watcher.close()

    async def i3_config_worker(self, watcher):
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            if event.name == '_config':
                with open(self.i3_path + "/config", "w") as fp:
                    subprocess.run(
                        ['ppi3', self.i3_path + '_config'],
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
                ["notify-send", check_config.encode('utf-8')]
            )
        check_config = ""

    def run_inotify_watchers(self):
        asyncio.ensure_future(self.mods_cfg_worker(self.mods_cfg_watcher()))
        asyncio.ensure_future(self.i3_config_worker(self.i3_config_watcher()))

    def run(self):
        def start(func, name, args=None):
            print(f'[{name} loading ', end='', flush=True)
            if args is None:
                func()
            elif args is not None:
                func(*args)
            print(f'... {name} loaded]', flush=True)

        use_inotify = True
        start(self.load_modules, 'modules')
        if use_inotify:
            start(self.run_inotify_watchers, 'inotify watchers')

        subprocess.run(['pkill', '-f', 'infod.py'])
        subprocess.run([self.i3_path + 'infod.py &'], shell=True)
        start(Thread(target=self.manager.mainloop,
              args=(self.loop,), daemon=True).start, 'mainloop')
        print('... everything loaded ...')
        notify_msg(self.notification_text)
        try:
            self.i3.main()
        except KeyboardInterrupt:
            self.i3.main_quit()
        print('... exit ...')


if __name__ == '__main__':
    get_lock('negi3mods.py')
    cgitb.enable(format='text')

    atexit.register(lambda: os._exit(0))

    daemon = Negi3Mods()
    daemon.run()

