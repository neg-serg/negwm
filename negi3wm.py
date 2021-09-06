#!/usr/bin/python3
""" negi3wm daemon script.
This module loads all negi3wm an start it via main's manager mailoop. Inotify-based watchers for all negi3wm S-expression-based
configuration spawned here, to use it just start it from any place without parameters. Moreover it contains pid-lock which prevents running
several times.

Usage:
    ./negi3wm.py [--debug|--tracemalloc|--start]

Options:
    --debug         disables signal handlers for debug.
    --tracemalloc   calculates and shows memory tracing with help of tracemalloc.
    --start         make actions for the start, not reloading

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2021
"""

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
import tracemalloc

from asyncinotify import Inotify, Mask
from docopt import docopt
import i3ipc
import psutil

from lib.checker import checker
from lib.locker import get_lock
from lib.misc import Misc
from lib.msgbroker import MsgBroker


class negi3wm():
    def __init__(self, cmd_args):
        """ Init function

            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """
        loop = asyncio.new_event_loop()
        self.tracemalloc_enabled = False
        self.show_load_time = False
        if cmd_args["--tracemalloc"]:
            self.tracemalloc_enabled = True

        if self.tracemalloc_enabled:
            tracemalloc.start()

        self.first_run = False
        if cmd_args["--start"]:
            self.first_run = True

        if not (cmd_args['--debug'] or self.tracemalloc_enabled):
            def loop_exit(signame):
                print(f"Got signal {signame}: exit")
                loop.stop()
                cleanup()

            for signame in ['SIGINT', 'SIGTERM']:
                loop.add_signal_handler(
                    getattr(signal, signame),
                    functools.partial(loop_exit, signame))
            loop.set_exception_handler(None)

        super().__init__()

        self.loop, self.mods = loop, {}
        extension = 'py'
        blacklist = {
            'cfg', 'checker', 'display', 'extension', 'geom', 'locker', 'misc',
            'msgbroker', 'matcher', 'negewmh', 'reflection', 'standalone_cfg',
            'sub', 'pub', '__init__'
        }
        mods = map(
            pathlib.Path,
            glob.glob(f"{os.path.dirname(sys.argv[0])}/lib/*.{extension}")
        )
        for mod in mods:
            if mod.is_file():
                name = str(mod.name).removesuffix(f'.{extension}')
                if name not in blacklist:
                    self.mods[sys.intern(name)] = None
        self.port = 15555
        self.echo = Misc.echo_on
        # main i3ipc connection created here and can be bypassed to the most of
        # modules here.
        self.i3 = i3ipc.Connection()

    @staticmethod
    def kill_proctree(pid, including_parent=True):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            if child.name() == 'negi3wm.py':
                child.kill()
                print(f'killed {child}')
        if including_parent:
            parent.kill()

    def load_modules(self):
        """ Load modules.
            This function init MsgBroker, use importlib to load all the
            stuff, then add_ipc and update notification with startup
            benchmarks.
        """
        mod_startup_times = []
        for mod in self.mods:
            start_time = timeit.default_timer()
            try:
                i3mod = importlib.import_module('lib.' + mod)
                self.mods[mod] = getattr(i3mod, mod)(self.i3)
            except ModuleNotFoundError:
                print(f'No such module as {mod}')
            try:
                self.mods[mod].asyncio_init(self.loop)
            except Exception:
                pass
            mod_startup_times.append(timeit.default_timer() - start_time)
        total_startup_time = str(round(sum(mod_startup_times), 6))
        loading_time_msg = f'[ok], load time {total_startup_time}'
        if self.show_load_time:
            self.echo(loading_time_msg)

    def autostart(self):
        """ Autostart auto negi3wm initialization """
        if self.first_run:
            circle = self.mods.get('circle')
            if circle is not None:
                circle.bindings['next']('term')

    async def cfg_mods_worker(self, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by default.
            watcher: watcher for cfg. """
        config_extension = '.py'
        while True:
            with Inotify() as inotify:
                inotify.add_watch(
                    f'{Misc.i3path()}/cfg/', Mask.MODIFY)
                async for event in inotify:
                    changed_mod = str(event.name).removesuffix(config_extension)
                    if changed_mod in self.mods:
                        binpath = f'{Misc.i3path()}/bin/'
                        subprocess.run(
                            [f'{binpath}/create_config.py'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            cwd=binpath, check=False
                        )
                        if reload_one:
                            self.mods[changed_mod].bindings['reload']()
                        else:
                            for mod in self.mods:
                                self.mods[mod].bindings['reload']()

    def run_config_watchers(self):
        """ Start all watchers in background via ensure_future """
        self.loop.create_task(self.cfg_mods_worker())

    def run(self):
        """ Run negi3wm here. """
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

        try:
            self.autostart()
            self.i3.main()
        except KeyboardInterrupt:
            self.i3.main_quit()


def cleanup():
    negi3wm.kill_proctree(os.getpid())

def main():
    """ Run negi3wm from here """
    get_lock(os.path.basename(__file__))
    # We need it because of thread_wait on Ctrl-C.
    atexit.register(cleanup)
    cmd_args = docopt(__doc__, version='0.9')
    wm = negi3wm(cmd_args)
    wm.run()
    if wm.tracemalloc_enabled:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        for stat in top_stats[:10]:
            print(stat)

if __name__ == '__main__':
    checker().check(verbose=False)
    main()
