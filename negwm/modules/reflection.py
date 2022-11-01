#!/usr/bin/env python
""" NegWM lib for reflection """
import asyncio
import sys
from negwm.lib.extension import extension

class reflection(extension):
    """ Class for reflection """
    def __init__(self, _) -> None:
        """ Init function
        Main part is in self.initialize, which performs initialization itself.
        i3: i3ipc connection """
        extension.__init__(self)

    @staticmethod
    async def echo(message):
        host, port = "::1", 15555
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=1.0)
        except asyncio.TimeoutError:
            print('Failed to connect NegWM')
            sys.exit(1)
        writer.write(message.encode())
        await writer.drain()
        data = await reader.read(2<<14)
        writer.close()
        await writer.wait_closed()
        return data

    @staticmethod
    async def run(message):
        host, port = "::1", 15555
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2.0)
        except asyncio.TimeoutError:
            print('Failed to connect NegWM')
            sys.exit(1)
        writer.write(message.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
