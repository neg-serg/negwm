""" Module contains routines used by several another modules.

Daemon manager and mod daemon:
    Mod daemon creates appropriate files in the /dev/shm directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.
"""

import asyncio
from contextlib import suppress


class MsgBroker():
    """ Daemon manager. Rules by negi3mods, dispatch messages.

        Every module has indivisual main loop with indivisual neg-ipc-file.
    """
    @classmethod
    def mainloop(cls, loop, mods, port) -> None:
        cls.mods = mods
        asyncio.set_event_loop(loop)
        loop.create_task(asyncio.start_server(
            cls.handle_client, 'localhost', port)
        )
        loop.run_forever()

    @classmethod
    async def handle_client(cls, reader, _) -> None:
        with suppress(Exception):
            while True:
                response = (await reader.read(255)).decode('utf8').split()
                name = response[0]
                cls.mods[name].send_msg(response[1:])

