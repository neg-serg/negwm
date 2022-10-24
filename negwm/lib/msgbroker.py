""" Module contains routines used by several another modules.
Daemon manager and mod daemon: Mod daemon creates appropriate files in the
/dev/shm directory. Daemon manager handles all requests to this named pipe
based API with help of asyncio. """

import asyncio
from typing import Dict

class MsgBroker():
    lock=asyncio.Lock()

    @classmethod
    def get_mods(cls) -> Dict:
        return cls.mods

    @classmethod
    def mainloop(cls, loop, mods, port) -> None:
        """ Mainloop by loop create task """
        cls.mods=mods
        loop.create_task(asyncio.start_server(
            cls.handle_client, 'localhost', port))
        loop.run_forever()

    @classmethod
    async def handle_client(cls, reader, _) -> None:
        """ Proceed client message here """
        async with cls.lock:
            while True:
                response=(await reader.readline()).decode('utf8').split()
                if not response:
                    return
                name=response[0]
                cls.mods[name].send_msg(response[1:])
