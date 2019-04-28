""" Module contains routines used by several another modules.

Daemon manager and mod daemon:
    Mod daemon creates appropriate files in the /dev/shm directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.
"""

import os
from contextlib import suppress
import asyncio
import aiofiles


class Manager():
    """ Daemon manager. Rules by negi3mods, dispatch messages.

        Every module has indivisual main loop with indivisual neg-ipc-file.
    """
    files = {}

    @classmethod
    async def ipc_listner(cls, name: str) -> None:
        """ Async neg-ipc-file listner

            Args:
                name(str): module name.
        """
        with suppress(Exception):
            while True:
                async with aiofiles.open(cls.files[name], mode='r') as fd:
                    while True:
                        data = await fd.read()
                        if not len(data):
                            break
                        eval_str = data.split('\n', 1)[0]
                        args = list(
                            filter(lambda x: x != '', eval_str.split(' '))
                        )
                        cls.mods[name].switch(args)

    @classmethod
    def create_ipc_object(cls, name: str) -> None:
        """ Add negi3mods IPC.
        """
        cls.files[name] = cls.create_ipc(name)

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

    @classmethod
    def mainloop(cls, loop, mods) -> None:
        """ Mainloop for module. Started by negi3mods in separated thread.

            Args:
                loop: asyncio.loop should be bypassed to function if you are
                using new thread.
        """
        cls.mods = mods
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.wait([cls.ipc_listner(m) for m in mods])
        )

    @classmethod
    def mainloop_socket(cls, loop, mods) -> None:
        cls.mods = mods
        asyncio.set_event_loop(loop)
        loop.create_task(asyncio.start_server(
            cls.handle_client, 'localhost', 15555)
        )
        loop.run_forever()

    @classmethod
    async def handle_client(cls, reader, writer):
        request = None
        while request != 'quit':
            response = str((await reader.read(255)).decode('utf8')) + '\n'
            rlist = response.split()
            name = rlist[0]
            del rlist[0]

            args = list(filter(lambda x: x != '', rlist))
            cls.mods[name].switch(args)

