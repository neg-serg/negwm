#!/usr/bin/python3
""" negwm daemon script.
This module loads all negwm an start it via main's manager mailoop. Inotify-based watchers for all negwm S-expression-based
configuration spawned here, to use it just start it from any place without parameters. Moreover it contains pid-lock which prevents running
several times.

Usage:
    ./negwm.py

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2022 """

import asyncio
import atexit
import functools
import glob
import importlib
import os
import pathlib
import signal
import subprocess
import sys
from threading import Thread
import timeit
import logging

from asyncinotify import Inotify, Mask
from docopt import docopt
import i3ipc
import psutil
from rich.traceback import install
from rich.console import Console

from lib.checker import checker
from lib.locker import get_lock
from lib.misc import Misc
from lib.msgbroker import MsgBroker

install(show_locals=True)
console = Console(log_time=True)

class negwm():
    def __init__(self):
        """ Init function

            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """
        logging.getLogger().setLevel(logging.INFO)
        loop = asyncio.new_event_loop()
        self.show_load_time = True

        def loop_exit(signame):
            logging.info(f"Got signal {signame}: exit")
            loop.stop()
            cleanup()

        for signame in ['SIGINT', 'SIGTERM']:
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(loop_exit, signame))
        loop.set_exception_handler(None)

        super().__init__()

        self.loop, self.mods = loop, {}
        blacklist = {'__init__'}
        mods = map(
            pathlib.Path,
            glob.glob(f"{os.path.dirname(sys.argv[0])}/modules/*.py")
        )
        for mod in mods:
            if mod.is_file():
                name = str(mod.name).removesuffix('.py')
                if name not in blacklist:
                    self.mods[sys.intern(name)] = None
        self.port = 15555
        # main i3ipc connection created here and can be bypassed to the most of
        # modules here.
        self.i3 = i3ipc.Connection()
        self.i3.on('binding', self.handle_bindings)

    def handle_bindings(self, _, event):
        data = event.ipc_data
        if data:
            cmd_str = data['binding']['command']
            if cmd_str[:3] == 'nop':
                cmd = cmd_str.split(',')[0].split()[1:]
                mod = cmd[0]
                if mod in self.mods:
                    args = ' '.join(cmd[2:]).split(',')[0].split()
                    mod_cmd = cmd[1]
                    try:
                        getattr(self.mods[mod], mod_cmd)(*args)
                    except TypeError:
                        print(f'Cannot call mod={self.mods[mod]} cmd={mod_cmd} args=({args})')

    @staticmethod
    def kill_proctree(pid, including_parent=True):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            if child.name() == 'negwm.py':
                child.kill()
                logging.info(f'killed {child}')
        if including_parent:
            parent.kill()

    def load_modules(self):
        """ Load modules.
            This function init MsgBroker, use importlib to load all the
            stuff, then add_ipc and update notification with startup
            benchmarks.
        """
        mod_startup_times = []
        console.status("[bold green]Loading...")
        for mod in self.mods:
            start_time = timeit.default_timer()
            i3mod = importlib.import_module('modules.' + mod)
            self.mods[mod] = getattr(i3mod, mod)(self.i3)
            try:
                self.mods[mod].asyncio_init(self.loop)
            except Exception:
                pass
            dt = timeit.default_timer() - start_time
            mod_startup_times.append(dt)
            logging.debug(f'{mod}: {round(dt,4)}')
            console.log(f"{mod}: {round(dt,5)}")
        total_startup_time = str(round(sum(mod_startup_times), 6))
        loading_time_msg = f'Total {total_startup_time}'
        logging.debug(loading_time_msg)
        console.log(loading_time_msg)


    async def cfg_mods_worker(self, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by default.
            watcher: watcher for cfg. """
        config_extension = '.cfg'
        while True:
            with Inotify() as inotify:
                inotify.add_watch(
                    f'{Misc.cfg_path()}/', Mask.MODIFY)
                async for event in inotify:
                    changed_mod = str(event.name).removesuffix(config_extension)
                    if changed_mod in self.mods:
                        binpath = f'{Misc.negwm_path()}/bin/'
                        subprocess.run(
                            [f'{binpath}/create_cfg'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=binpath, check=False
                        )
                        if reload_one:
                            self.mods[changed_mod].reload()
                        else:
                            for mod in self.mods:
                                self.mods[mod].reload()

    def run_config_watchers(self):
        """ Start all watchers in background via ensure_future """
        self.loop.create_task(self.cfg_mods_worker())

    def create_config(self):
        binpath = f'{Misc.negwm_path()}/bin/'
        subprocess.run(
            [f'{binpath}/create_cfg', '-d'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=binpath, check=False)
        mod, mod_cmd = 'conf_gen', 'write'
        getattr(self.mods[mod], mod_cmd)()
        subprocess.run(['i3-msg', 'reload'])

    def run(self):
        """ Run negwm here. """
        def start(func, args=None):
            """ Helper for pretty-printing of loading process.
                func (callable): callable routine to run.
                args: routine args, optional.
            """
            if args is None:
                func()
            elif args is not None:
                func(*args)
        start(self.load_modules)
        start(self.run_config_watchers)
        # Start modules mainloop.
        mainloop = Thread(
            target=MsgBroker.mainloop,
            args=(self.loop, self.mods, self.port,),
            daemon=True
        )
        start((mainloop).start)

        if Misc.i3_cfg_need_dump():
            self.create_config()

        try:
            self.i3.main()
        except KeyboardInterrupt:
            self.i3.main_quit()

def cleanup():
    negwm.kill_proctree(os.getpid())

def main():
    """ Run negwm from here """
    get_lock(os.path.basename(__file__))
    # We need it because of thread_wait on Ctrl-C.
    atexit.register(cleanup)
    docopt(str(__doc__), version='0.9.1')
    wm = negwm()
    wm.run()

if __name__ == '__main__':
    checker().check()
    main()
