#!/usr/bin/python3

""" i3 negi3wm daemon script.

This module loads all negi3wm an start it via main's manager
mailoop. Inotify-based watchers for all negi3wm TOML-based configuration
spawned here, to use it just start it from any place without parameters. Also
there is i3 config watcher to convert it from ppi3 format to plain i3
automatically. Moreover it contains pid-lock which prevents running several
times.

Usage:
    ./negi3wm.py [--debug|--tracemalloc|--start]

Options:
    --debug         disables signal handlers for debug.
    --tracemalloc   calculates and shows memory tracing with help of
                    tracemalloc.
    --start         make actions for the start, not reloading

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2020

"""

import os
import timeit
import atexit
import sys
import subprocess
import signal
import functools
import importlib
import shutil
from threading import Thread

for m in ["inotipy", "i3ipc", "docopt", "pulsectl",
          "qtoml", "Xlib", "yaml", "yamlloader", "ewmh"]:
    if sys.version_info >= (3, 5):
        if not importlib.util.find_spec(m):
            print(f"Cannot import [{m}], please install")
    elif not importlib.find_loader(m):
        print(f"Cannot import [{m}], please install")


import asyncio
import inotipy

import i3ipc
from docopt import docopt

from lib.locker import get_lock
from lib.msgbroker import MsgBroker
from lib.misc import Misc
from lib.standalone_cfg import modconfig
from lib.checker import checker


class negi3wm(modconfig):
    def __init__(self, cmd_args):
        """ Init function

            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """
        loop = asyncio.new_event_loop()
        self.tracemalloc_enabled = False
        if cmd_args["--tracemalloc"]:
            self.tracemalloc_enabled = True
            import tracemalloc

        if self.tracemalloc_enabled:
            tracemalloc.start()

        self.first_run = False
        if cmd_args["--start"]:
            self.first_run = True

        if not (cmd_args['--debug'] or self.tracemalloc_enabled):
            def loop_exit(signame):
                print(f"Got signal {signame}: exit")
                loop.stop()
                os._exit(0)

            for signame in {'SIGINT', 'SIGTERM'}:
                loop.add_signal_handler(
                    getattr(signal, signame),
                    functools.partial(loop_exit, signame))
            loop.set_exception_handler(None)

        modconfig.__init__(self)

        self.loop = loop
        self.mods = {}
        for mod in self.conf("module_list"):
            self.mods[sys.intern(mod)] = None

        self.prepare_notification_text()

        # test config to check ppi3 conversion result
        self.test_cfg_path = os.path.realpath(
            os.path.expandvars('$HOME/tmp/config_test')
        )

        self.port = int(self.conf('port'))

        self.echo = Misc.echo_on
        self.notify = Misc.notify_off

        # main i3ipc connection created here and can be bypassed to the most of
        # modules here.
        self.i3 = i3ipc.Connection()

    def prepare_notification_text(self):
        """ stuff for startup notifications """
        self.notification_text = "Starting negi3wm\n\n"
        notification_color_field = self.conf("notification_color_field")
        notification_color = Misc.extract_xrdb_value(notification_color_field) \
            or '#395573'
        prefix = self.conf("prefix")
        self.msg_prefix = f"<span weight='normal' \
            color='{notification_color}'> {prefix} </span>"

    def load_modules(self):
        """ Load modules.

            This function init MsgBroker, use importlib to load all the
            stuff, then add_ipc and update notification with startup
            benchmarks.
        """
        mod_startup_times = []
        self.echo('Loading modules')
        for mod in self.mods:
            start_time = timeit.default_timer()
            i3mod = importlib.import_module('lib.' + mod)
            self.mods[mod] = getattr(i3mod, mod)(self.i3)
            try:
                self.mods[mod].asyncio_init(self.loop)
            except Exception:
                pass
            mod_startup_times.append(timeit.default_timer() - start_time)
            time_elapsed = f'{mod_startup_times[-1]:4f}s'
            mod_loaded_info = f'{mod:<10s} ~ {time_elapsed:>10s}'
            self.notification_text += self.msg_prefix + mod_loaded_info + '\n'
            self.echo(mod_loaded_info, flush=True)
        loading_time_msg = f'Loading time = {sum(mod_startup_times):6f}s'
        self.notification_text += loading_time_msg
        self.echo(loading_time_msg)

    def cfg_mods_watcher(self):
        """ cfg watcher to update modules config in realtime. """
        watcher = inotipy.Watcher.create()
        watcher.watch(Misc.i3path() + '/cfg/', inotipy.IN.MODIFY)
        return watcher

    def autostart(self):
        """ Autostart auto negi3wm initialization """
        if self.first_run:
            Misc.send(['circle next term'], i3=self.i3)

    def cfg_i3_watcher(self):
        """ i3 config watcher to run ppi3 on write. """
        watcher = inotipy.Watcher.create()
        watcher.watch(Misc.i3path(), inotipy.IN.CLOSE_WRITE)
        return watcher

    async def cfg_mods_worker(self, watcher, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by
            default.

            Args:
                watcher: watcher for cfg.
        """
        while True:
            event = await watcher.get()
            changed_mod = event.pathname[:-4]
            if changed_mod in self.mods:
                if reload_one:
                    Misc.send([changed_mod, 'reload'], i3=self.i3)
                    self.notify(f'[Reloaded {changed_mod}]')
                else:
                    for mod in self.mods:
                        Misc.send([mod, 'reload'], i3=self.i3)
                    self.notify(
                        '[Reloaded {' + ','.join(self.mods.keys()) + '}]'
                    )

    async def cfg_i3_worker(self, watcher):
        """ Run ppi3 when config is changed

            Args:
                watcher: watcher for i3 config.
        """
        while True:
            event = await watcher.get()
            config_is_valid = False
            if event.pathname == '_config':
                with open(self.test_cfg_path, "w") as fconf:
                    try:
                        subprocess.run(
                            ['ppi3', Misc.i3path() + '_config'],
                            stdout=fconf,
                            check=True
                        )
                        config_is_valid = Misc.validate_i3_config(
                            self.test_cfg_path, remove=True
                        )
                    except subprocess.CalledProcessError as proc_err:
                        Misc.print_run_exception_info(proc_err)
                if config_is_valid:
                    self.echo("i3 config is valid!")
                    shutil.move(self.test_cfg_path, Misc.i3path() + 'config')

    def run_config_watchers(self):
        """ Start all watchers here via ensure_future to run it in background.
        """
        asyncio.ensure_future(self.cfg_mods_worker(self.cfg_mods_watcher()))
        asyncio.ensure_future(self.cfg_i3_worker(self.cfg_i3_watcher()))

    def run(self):
        """ Run negi3wm here. """
        def start(func, args=None):
            """ Helper for pretty-printing of loading process.

                Args:
                    func (callable): callable routine to run.
                    name: routine name.
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

        self.echo('... everything loaded ...')
        self.notify(self.notification_text)
        try:
            self.autostart()
            self.i3.main()
        except KeyboardInterrupt:
            self.i3.main_quit()
        self.echo('... exit ...')


def main():
    """ Run negi3wm from here """
    get_lock(os.path.basename(__file__))

    # We need it because of thread_wait on Ctrl-C.
    atexit.register(lambda: os._exit(0))

    cmd_args = docopt(__doc__, version='0.8')

    negi3wm_instance = negi3wm(cmd_args)
    negi3wm_instance.run()

    if negi3wm_instance.tracemalloc_enabled:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        print("[ Top 10 ]")
        for stat in top_stats[:10]:
            print(stat)

if __name__ == '__main__':
    checker().check(verbose=False)
    main()
