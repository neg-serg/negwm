#!/usr/bin/pypy3 -u
import asyncio
import i3ipc
import sys
from threading import Thread, Event


class ws_watcher():
    def __init__(self):
        self.event = Event()
        self.event.set()

        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.on_ws_focus)

        self.loop = asyncio.get_event_loop()
        self.ws_str = "ws"

        self.addr = "0.0.0.0"
        self.port = "31888"
        self.buf_size = 1024
        self.status = "none"

    def on_ws_focus(self, i3, event):
        self.event.set()

    def main(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(
            asyncio.wait([
                self.update_status(self.loop),
            ])
        )

    async def update_status(self, loop):
        while True:
            if self.event.wait():
                reader, writer = await asyncio.open_connection(
                    host=self.addr, port=self.port, loop=loop
                )
                writer.write(self.ws_str.encode(encoding='utf-8'))
                stat_data = await reader.read(self.buf_size)
                sys.stdout.write(f"{stat_data.decode('utf-8')}\n")
                self.event.clear()


if __name__ == '__main__':
    loop = ws_watcher()
    Thread(target=loop.main, daemon=True).start()
    loop.i3.main()

