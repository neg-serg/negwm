#!/usr/bin/pypy3 -u
from gevent import monkey
monkey.patch_all()

import asyncio
import lib.i3ipc as i3ipc
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
        self.ws_name = ""

        self.binding_mode = ""
        self.mode_regex = re.compile('.*mode ')
        self.split_by = re.compile('[;,]')

        self.ws_color = "#8FA8C7"
        self.ws_name = ""
        for ws in self.i3.get_workspaces():
            if ws.focused:
                self.ws_name = ws.name
                break

    def on_ws_focus(self, i3, event):
        self.ws_name = event.current.name
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
            self.update_status(self.loop),
        )

    async def update_status(self, loop):
        while True:
            if self.event.wait():
                ws = self.ws_name
                if not ws[0].isalpha():
                    ws = self.colorize(ws[0], color="#8FA8C7") + ws[1:]
                sys.stdout.write(f"{self.binding_mode + ws}\n")
                self.event.clear()
                await asyncio.sleep(0)


if __name__ == '__main__':
    loop = ws_watcher()
    Thread(target=loop.main, daemon=False).start()
    loop.i3.main()

