#!/usr/bin/pypy3
""" i3 negi3mods daemon script.

This module loads all negi3mods an start it via modlib's daemon_manager
mailoop. Inotify-based watchers for all negi3mods TOML-based configuration
spawned here, to use it just start it from any place without parameters. Also
there is i3 config watcher to convert it from ppi3 format to plain i3
automatically. Moreover it contains pid-lock which prevents running several
times.

Usage:
    negi3mods.py

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2018

"""

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
        """ Init function

            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """
        self.mods = {
            intern('circle'): None,
            intern('ns'): None,
            intern('flast'): None,
            intern('menu'): None,
            intern('fsdpms'): None,
            intern('wm3'): None,
            intern('vol'): None,
        }

        # stuff for startup notifications
        self.notification_text = "Wow! It's time to start mods!\n\n"
        self.msg_prefix = "<span weight='normal' color='#395573'> >> </span>"

        # i3 path used to get i3 config path for "send" binary, _config needed
        # by ppi3 path and another configs.
        self.i3_path = i3path()

        # i3 path used to get "send" binary path
        self.i3_cfg_path = self.i3_path + '/cfg/'

        # main i3ipc connection created here and can be bypassed to the most of modules here.
        self.i3 = i3ipc.Connection()

        # setup asyncio loop
        self.loop = asyncio.get_event_loop()

    def load_modules(self):
        """ Load modules.

            This function init daemon_manager, use importlib to load all the
            stuff, then add_fifo and update notification with startup
            benchmarks.
        """
        mod_startup_times = []
        self.manager = daemon_manager(self.mods)
        print()
        for mod in self.mods.keys():
            start_time = timeit.default_timer()
            i3mod = importlib.import_module(mod + "d")
            self.mods[mod] = getattr(i3mod, mod)(self.i3, loop=self.loop)
            self.manager.add_fifo(mod)
            mod_startup_times.append(timeit.default_timer() - start_time)
            time_elapsed = f'{mod_startup_times[-1]:4f}s'
            mod_text = f'[{mod}]'
            mod_loaded_info = f'Loaded {mod_text:<10s} ~ {time_elapsed:>10s}'
            self.notification_text += self.msg_prefix + mod_loaded_info + '\n'
            print(mod_loaded_info, flush=True)
        overall_msg = f'Overall time = {sum(mod_startup_times):6f}s'
        self.notification_text += overall_msg
        print(overall_msg)

    def mods_cfg_watcher(self):
        """ modi3cfg watcher to update modules config in realtime.
        """
        watcher = aionotify.Watcher()
        watcher.watch(alias='configs', path=self.i3_cfg_path,
                      flags=aionotify.Flags.MODIFY)
        return watcher

    def i3_config_watcher(self):
        """ i3 config watcher to run ppi3 on write.
        """
        watcher = aionotify.Watcher()
        watcher.watch(
            alias='i3cfg',
            path=self.i3_path,
            flags=aionotify.Flags.CLOSE_WRITE,
        )
        return watcher

    async def mods_cfg_worker(self, watcher, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by
            default.

            Args:
                watcher: watcher for modi3cfg.
        """
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            changed_mod = event.name[:-4]
            if changed_mod in self.mods:
                if reload_one:
                    subprocess.run([self.i3_path + 'send', changed_mod, 'reload'])
                    notify_msg(f'[Reloaded {changed_mod}]')
                else:
                    for mod in self.mods.keys():
                        subprocess.run([self.i3_path + 'send', mod, 'reload'])
                    notify_msg('[Reloaded {' + ','.join(self.mods.keys()) + '} ]')
        watcher.close()

    async def i3_config_worker(self, watcher):
        """ Run ppi3 when config is changed

            Args:
                watcher: watcher for i3 config.
        """
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
        """ Checks i3 config.

            TODO: add this check to the i3 watcher again.
        """
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
        """ Start all watchers here via ensure_future to run it in background.
        """
        asyncio.ensure_future(self.mods_cfg_worker(self.mods_cfg_watcher()))
        asyncio.ensure_future(self.i3_config_worker(self.i3_config_watcher()))

    def run(self):
        """ Run negi3mods here.
        """
        def start(func, name, args=None):
            """ Helper for pretty-printing of loading process.

                Args:
                    func (callable): callable routine to run.
                    name: routine name.
                    args: routine args, optional.
            """
            print(f'[{name} loading ', end='', flush=True)
            if args is None:
                func()
            elif args is not None:
                func(*args)
            print(f'... {name} loaded]', flush=True)

        # Start inotify watchers
        use_inotify = True
        start(self.load_modules, 'modules')
        if use_inotify:
            start(self.run_inotify_watchers, 'inotify watchers')

        # Start echo server as separated process
        subprocess.run(['pkill', '-f', 'infod.py'])
        subprocess.run([self.i3_path + 'infod.py &'], shell=True)

        # Start modules mainloop.
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

    # We need it because of thread_wait on Ctrl-C.
    atexit.register(lambda: os._exit(0))

    daemon = Negi3Mods()
    daemon.run()

