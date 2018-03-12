#!/usr/bin/pypy3 -u
import asyncio
import sys
from threading import Thread


class volume_watcher():
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        self.ws_str = "v"
        self.addr = "127.0.0.1"
        self.port = "6600"
        self.buf_size = 1024
        self.volume = ""
        self.idle_mixer = "idle mixer\n"
        self.status_cmd_str = "status\n"

    def main(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(
            self.update_mpd_volume(self.loop),
        )

    async def update_mpd_volume(self, loop):
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port, loop=loop
        )
        data = await reader.read(self.buf_size)
        writer.write(self.status_cmd_str.encode(encoding='utf-8'))
        stat_data = await reader.read(self.buf_size)
        parsed = stat_data.decode('UTF-8').split('\n')
        if 'volume' in parsed[0]:
            self.volume = parsed[0][8:]
            self.volume = f'%{{F#395573}} || %{{F-}}%{{F#cccccc}}Vol: {self.volume}%%{{F-}}%{{F#395573}} ⟭%{{F-}}'
            sys.stdout.write(f"{self.volume}\n")
        if data.startswith(b'OK'):
            while True:
                writer.write(self.idle_mixer.encode(encoding='utf-8'))
                data = await reader.read(self.buf_size)
                if data.decode('UTF-8'):
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.buf_size)
                    parsed = stat_data.decode('UTF-8').split('\n')
                    if 'volume' in parsed[0]:
                        self.volume = parsed[0][8:]
                        self.volume = f'%{{F#395573}} || %{{F-}}%{{F#cccccc}}Vol: {self.volume}%%{{F-}}%{{F#395573}} ⟭%{{F-}}'
                        sys.stdout.write(f"{self.volume}\n")


if __name__ == '__main__':
    loop = volume_watcher()
    Thread(target=loop.main, daemon=False).start()

