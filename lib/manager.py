""" Module contains routines used by several another modules.

Daemon manager and mod daemon:
    Mod daemon creates appropriate files in the /dev/shm directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.
"""

import asyncio


class Manager():
    """ Daemon manager. Rules by negi3mods, dispatch messages.

        Every module has indivisual main loop with indivisual neg-ipc-file.
    """
    @classmethod
    def mainloop(cls, loop, mods) -> None:
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

