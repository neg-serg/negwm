""" MsgBroker handles all requests to mods in format like this:
    <mod> <cmd> <arguments>
    To use it you can run smth like this for example:
    echo 'circle next web' | nc localhost 15555 -N """

import asyncio
import pickle
from typing import Dict, List

class MsgBroker():
    lock=asyncio.Lock()

    @classmethod
    def get_mods(cls) -> Dict:
        return cls.mods

    @classmethod
    def get_mods_list(cls) -> List:
        return cls.mods.keys()

    @classmethod
    def mainloop(cls, loop, mods, port) -> None:
        """ Mainloop by loop create task """
        cls.mods=mods
        loop.create_task(asyncio.start_server(
            cls.handle_client, 'localhost', port))
        loop.run_forever()

    @classmethod
    async def handle_client(cls, reader, writer) -> None:
        """ Proceed client message here """
        async with cls.lock:
            while True:
                response=(await reader.readline()).decode('utf8').split()
                if not response:
                    return
                name=response[0]
                ret = cls.mods[name].send_msg(response[1:])
                if ret:
                    writer.write(pickle.dumps(ret))
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
