#!/usr/bin/pypy3 -u
import asyncio
import i3ipc
import sys
import re
from threading import Thread, Event


class ws_watcher():
    def __init__(self):
        self.event = Event()
        self.event.set()

        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.i3.on('binding', self.on_eventent)

        self.loop = asyncio.get_event_loop()
        self.ws_str = "ws"

        self.binding_mode = ""
        self.mode_regex = re.compile('.*mode ')
        self.split_by = re.compile('[;,]')

        self.addr = "0.0.0.0"
        self.port = "31888"
        self.buf_size = 1024
        self.status = "none"

    def on_ws_focus(self, i3, event):
        self.event.set()

    def colorize(self, s, color="#005fd7"):
        return f"%{{F{color}}}{s}%{{F#ccc}}"

    def on_eventent(self, i3, event):
        bind_cmd = event.binding.command
        for t in re.split(self.split_by, bind_cmd):
            if 'mode' in t:
                ret = re.sub(self.mode_regex, '', t)
                if ret[0] == ret[-1] and ret[0] in {'"', "'"}:
                    ret = ret[1:-1]
                    if ret == "default":
                        self.binding_mode = ''
                    else:
                        self.binding_mode = self.colorize(ret) + ' '
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
                ws = await reader.read(self.buf_size)
                ws = ws.decode('utf-8')
                if not ws[0].isalpha():
                    ws = self.colorize(ws[0], color="#8FA8C7") + ws[1:]
                sys.stdout.write(f"{self.binding_mode + ws}\n")
                self.event.clear()


if __name__ == '__main__':
    loop = ws_watcher()
    Thread(target=loop.main, daemon=True).start()
    loop.i3.main()

