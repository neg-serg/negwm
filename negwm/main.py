#!/usr/bin/python3
""" 
NegWM daemon script.
This module loads all negwm an start it via main's manager mailoop. Inotify-based watchers for all negwm S-expression-based
configuration spawned here, to use it just start it from any place without parameters. Moreover it contains pid-lock which prevents running
several times.

Usage:
    main.py [-diqv] [--systemd]
    main.py -d, --debug
    main.py -i, --info
    main.py -q, --quiet
    main.py -v, --verbose
    main.py --systemd

Options:
    -d, --debug       Enable debug mode with debug logging
    -i, --info        Info logging
    -q, --quiet       Quiet, no logging
    -v, --verbose     More verbose logging
    --systemd         Use systemd for logging

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

import negwm
from negwm.lib.checker import checker
from negwm.lib.locker import get_lock
from negwm.lib.misc import Misc
from negwm.lib.msgbroker import MsgBroker

install(show_locals=True)
console=Console(log_time=True)

class NegWM():
    def __init__(self):
        """ Init function
            Using of self.intern for better performance, create i3ipc
            connection, connects to the asyncio eventloop.
        """
        loop=asyncio.new_event_loop()

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

        self.loop, self.mods=loop, {}
        blacklist={'__init__'}
        dirname=os.path.dirname
        mods=map(
            pathlib.Path,
            glob.glob(f"{dirname(dirname(negwm.__file__))}/negwm/modules/*.py")
        )
        for mod in mods:
            if mod.is_file():
                name=str(mod.name).removesuffix('.py')
                if name not in blacklist:
                    self.mods[sys.intern(name)]=None
        self.port=15555
        # main i3ipc connection created here and can be bypassed to the most of
        # modules here.
        self.i3=i3ipc.Connection()
        self.i3.on('binding', self.handle_bindings)

    def handle_bindings(self, _, event):
        data=event.ipc_data
        if data:
            cmd_str=data['binding']['command']
            if cmd_str[:3] == 'nop':
                cmd=cmd_str.split(',')[0].split()[1:]
                mod=cmd[0]
                if mod in self.mods:
                    args=' '.join(cmd[2:]).split(',')[0].split()
                    mod_cmd=cmd[1]
                    try:
                        getattr(self.mods[mod], mod_cmd)(*args)
                    except TypeError:
                        logging.info(f'Cannot call mod={self.mods[mod]} cmd={mod_cmd} args=({args})')

    @staticmethod
    def kill_proctree(pid, including_parent=True):
        parent=psutil.Process(pid)
        for child in parent.children(recursive=True):
            if child.name() == os.path.basename(__file__):
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
        mod_startup_times=[]
        console.status("[bold green]Loading...")
        for mod in self.mods:
            start_time=timeit.default_timer()
            i3mod=importlib.import_module('negwm.modules.' + mod)
            self.mods[mod]=getattr(i3mod, mod)(self.i3)
            try:
                self.mods[mod].asyncio_init(self.loop)
            except Exception:
                pass
            dt=timeit.default_timer() - start_time
            mod_startup_times.append(dt)
            logging.debug(f'{mod}: {round(dt,4)}')
            console.log(f"{mod}: {round(dt,5)}")
        total_startup_time=str(round(sum(mod_startup_times), 6))
        loading_time_msg=f'Total {total_startup_time}'
        logging.debug(loading_time_msg)
        console.log(loading_time_msg)

    def create_config_cache(self):
        binpath=f'{os.path.dirname(negwm.__file__)}/bin/'
        subprocess.run(
            [f'{binpath}/create_cfg'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=binpath, check=True
        )

    async def cfg_mods_worker(self, reload_one=True):
        """ Reloading configs on change. Reload only appropriate config by default.
            watcher: watcher for cfg. """
        config_extension='.cfg'
        while True:
            with Inotify() as inotify:
                inotify.add_watch(
                    f'{Misc.cfg_path()}/', Mask.MODIFY)
                async for event in inotify:
                    changed_mod=str(event.name).removesuffix(config_extension)
                    if changed_mod in self.mods:
                        self.create_config_cache()
                        if reload_one:
                            self.mods[changed_mod].reload()
                        else:
                            for mod in self.mods:
                                self.mods[mod].reload()

    def run_config_watchers(self):
        """ Start all watchers in background via ensure_future """
        self.loop.create_task(self.cfg_mods_worker())

    def create_config(self):
        binpath=f'{os.path.dirname(negwm.__file__)}/bin/'
        subprocess.run(
            [f'{binpath}/create_cfg', '-d'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=binpath, check=True)
        mod, mod_cmd='conf_gen', 'write'
        getattr(self.mods[mod], mod_cmd)()
        subprocess.run(['i3-msg', 'reload'])

    def startup(self):
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
        mainloop=Thread(
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
    NegWM.kill_proctree(os.getpid())

def main():
    """ Run negwm from here """
    get_lock(os.path.basename(__file__))
    # We need it because of thread_wait on Ctrl-C.
    atexit.register(cleanup)
    arguments=docopt(str(__doc__), version='0.9.2')
    log=logging.getLogger()
    if arguments['--systemd']:
        from systemd import journal
        log.addHandler(journal.JournalHandler())
    loglevel=logging.INFO
    if arguments['--debug'] or arguments['--verbose']:
        loglevel=logging.DEBUG
    elif arguments['--info']:
        loglevel=logging.INFO
    elif arguments['--quiet']:
        loglevel=logging.CRITICAL
    else:
        log.setLevel(loglevel)
    wm=NegWM()
    wm.create_config_cache()
    wm.startup()

def run():
    checker().check()
    main()

if __name__ == '__main__':
    run()
