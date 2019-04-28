#!/usr/bin/pypy3

""" i3 negi3mods daemon script.

This module loads all negi3mods an start it via main's manager
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
year :: 2019

"""

import os
import timeit
import atexit
import sys
import subprocess
import importlib
import shutil
from threading import Thread

import asyncio
import aionotify

import i3ipc

from lib.locker import get_lock
from lib.manager import Manager
from lib.misc import Misc
from lib.standalone_cfg import modconfig


class negi3mods(modconfig):
    def __init__(self):
        """ Init function

            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """

        # i3 path used to get i3 config path for "send" binary, _config needed
        # by ppi3 path and another configs.
        self.i3_path = Misc.i3path()

        # setup asyncio loop
        loop = asyncio.get_event_loop()

        modconfig.__init__(self, loop)

        self.loop = loop
        self.mods = {}
        for mod in self.conf("module_list"):
            self.mods[sys.intern(mod)] = None

        self.prepare_notification()

        # i3 path used to get "send" binary path
        self.i3_cfg_path = self.i3_path + '/cfg/'

        # test config to check ppi3 conversion result
        self.test_cfg_path = os.path.realpath(
            os.path.expandvars('$HOME/tmp/config_test')
        )

        # main i3ipc connection created here and can be bypassed to the most of
        # modules here.
        self.i3 = i3ipc.Connection()

    def prepare_notification(self):
        # stuff for startup notifications
        self.notification_text = "Wow! It's time to start mods!\n\n"
        notification_color_field = self.conf("notification_color_field")
        notification_color = Misc.extract_xrdb_value(notification_color_field)
        prefix = self.conf("prefix")
        self.msg_prefix = f"<span weight='normal' \
                           color='{notification_color}'> {prefix} </span>"

    def load_modules(self):
        """ Load modules.

            This function init Manager, use importlib to load all the
            stuff, then add_ipc and update notification with startup
            benchmarks.
        """
        mod_startup_times = []
        print()
        for mod in self.mods.keys():
            start_time = timeit.default_timer()
            i3mod = importlib.import_module('lib.' + mod)
            self.mods[mod] = getattr(i3mod, mod)(self.i3, loop=self.loop)
            Manager.create_ipc_object(mod)
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
        """ cfg watcher to update modules config in realtime.
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
            flags=aionotify.Flags.CLOSE_WRITE
        )
        return watcher

    async def mods_cfg_worker(self, watcher, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by
            default.

            Args:
                watcher: watcher for cfg.
        """
        await watcher.setup(self.loop)
        while True:
            event = await watcher.get_event()
            changed_mod = event.name[:-4]
            if changed_mod in self.mods:
                if reload_one:
                    subprocess.run(
                        [self.i3_path + 'send', changed_mod, 'reload']
                    )
                    Misc.notify_msg(f'[Reloaded {changed_mod}]')
                else:
                    for mod in self.mods.keys():
                        subprocess.run(
                            [self.i3_path + 'send', mod, 'reload']
                        )
                    Misc.notify_msg(
                        '[Reloaded {' + ','.join(self.mods.keys()) + '} ]'
                    )
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
                with open(self.test_cfg_path, "w") as fp:
                    subprocess.run(
                        ['ppi3', self.i3_path + '_config'],
                        stdout=fp
                    )
                    config_is_valid = self.validate_i3_config()
                if config_is_valid:
                    print("i3 config is valid!")
                    shutil.move(self.test_cfg_path, self.i3_path + 'config')
        watcher.close()

    def validate_i3_config(self):
        """ Checks that i3 config is ok.
        """
        check_config = subprocess.run(
            ['i3', '-c', self.test_cfg_path, '-C'],
            stdout=subprocess.PIPE
        ).stdout.decode('utf-8')
        if len(check_config):
            error_data = check_config.encode('utf-8')
            print(error_data)
            subprocess.Popen(["notify-send", error_data])

            # remove invalid config
            os.remove(self.test_cfg_path)

            return False
        return True

    def run_inotify_watchers(self):
        """ Start all watchers here via ensure_future to run it in background.
        """
        asyncio.ensure_future(self.mods_cfg_worker(self.mods_cfg_watcher()))
        asyncio.ensure_future(self.i3_config_worker(self.i3_config_watcher()))

    def run_procs(self):
        for proc in self.conf("proc_list"):
            # Start echo server as separated process
            subprocess.run(['pkill', '-f', f'proc.{proc}'])
            subprocess.run(
                [sys.executable + f' -m proc.{proc} &'],
                shell=True,
                cwd=self.i3_path
            )
            print(f'run module proc.{proc}')

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

        start(self.load_modules, 'modules')
        start(self.run_inotify_watchers, 'inotify watchers')

        self.run_procs()

        # Start modules mainloop.
        mainloop_socket = Thread(
            target=Manager.mainloop_socket,
            args=(self.loop, self.mods,),
            daemon=True
        )
        start((mainloop_socket).start, 'mainloop_socket')

        print('... everything loaded ...')
        Misc.notify_msg(self.notification_text)
        try:
            self.i3.main()
        except KeyboardInterrupt:
            self.i3.main_quit()
        print('... exit ...')


if __name__ == '__main__':
    get_lock(os.path.basename(__file__))

    # We need it because of thread_wait on Ctrl-C.
    atexit.register(lambda: os._exit(0))

    negi3mods().run()

