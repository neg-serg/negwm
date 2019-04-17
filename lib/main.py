""" Module contains routines used by several another modules.

There are several superclasses and generic modules here.
The main reason is "don't repeat yourself", DRY.

Matcher:
    Matcher: class to check that window can be tagged with given tag by
    WM_CLASS, WM_INSTANCE, regexes, etc. It can be used by named scrachpad,
    circle run-or-raise, etc.

Daemon manager and mod daemon:
    Mod daemon creates appropriate files in the /dev/shm directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.

"""

import os
import asyncio
import aiofiles
from typing import List

from singleton import Singleton


class daemon_manager():
    """ Daemon manager. Rules by negi3mods, dispatch messages.

        Every module has indivisual main loop with indivisual neg-ipc-file.

    Metaclass:
        Use Singleton metaclass from singleton module.
    """
    __metaclass__ = Singleton

    def __init__(self, mods: List) -> None:
        self.files = {}  # file list
        self.mods = mods  # mods list

    async def ipc_listner(self, name: str) -> None:
        """ Async neg-ipc-file listner

            Args:
                name(str): module name.
        """
        while True:
            async with aiofiles.open(self.files[name], mode='r') as fd:
                while True:
                    data = await fd.read()
                    if not len(data):
                        break
                    eval_str = data.split('\n', 1)[0]
                    args = list(filter(lambda x: x != '', eval_str.split(' ')))
                    try:
                        self.mods[name].switch(args)
                    except Exception:
                        pass

    def add_ipc(self, name: str) -> None:
        """ Add negi3mods IPC.
        """
        self.files[name] = self.create_ipc(name)

    @staticmethod
    def create_ipc(name: str) -> str:
        """ Create IPC for the given name
        """
        neg_ipc_file = os.path.realpath(os.path.expandvars(
            '/dev/shm/' + name + '.nif'))
        if os.path.exists(neg_ipc_file):
            os.remove(neg_ipc_file)
        try:
            os.mkfifo(neg_ipc_file)
        except OSError as oe:
            if oe.errno != os.errno.EEXIST:
                raise
        finally:
            return neg_ipc_file

    def mainloop(self, loop) -> None:
        """ Mainloop for module. Started by negi3mods in separated thread.

            Args:
                loop: asyncio.loop should be bypassed to function if you are
                using new thread.
        """
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.wait([self.ipc_listner(m) for m in self.mods])
        )

