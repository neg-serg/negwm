#!/usr/bin/pypy3 -u
import asyncio
import sys


class volume_watcher():
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        self.ws_str = "v"
        self.addr = "127.0.0.1"
        self.port = "6600"
        self.buf_size = 1024
        self.volume = ""
        self.idle_mixer = "idle mixer player\n"
        self.status_cmd_str = "status\n"

    def main(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(
            self.update_mpd_volume(self.loop),
        )

    def pretty_printing(self, string):
        return f'%{{F#395573}} || %{{F-}}%{{F#cccccc}}' + \
            f'Vol: {string}%%{{F-}}%{{F#395573}} ⟭%{{F-}}'

    async def update_mpd_volume(self, loop):
        prev_volume = 0
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port, loop=loop
        )
        data = await reader.read(self.buf_size)
        writer.write(self.status_cmd_str.encode(encoding='utf-8'))
        stat_data = await reader.read(self.buf_size)
        parsed = stat_data.decode('UTF-8').split('\n')
        if 'volume' in parsed[0]:
            self.volume = parsed[0][8:]
            if int(self.volume) >= 0:
                self.volume = self.pretty_printing(self.volume)
                sys.stdout.write(f"{self.volume}\n")
            else:
                sys.stdout.write(f" \n")
        if data.startswith(b'OK'):
            while True:
                writer.write(self.idle_mixer.encode(encoding='utf-8'))
                data = await reader.read(self.buf_size)
                if data.decode('UTF-8'):
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.buf_size)
                    parsed = stat_data.decode('UTF-8').split('\n')
                    if 'state: play' in parsed:
                        if 'volume' in parsed[0]:
                            self.volume = parsed[0][8:]
                            if int(self.volume) >= 0:
                                if prev_volume != self.volume:
                                    self.volume = self.pretty_printing(self.volume)
                                    sys.stdout.write(f"{self.volume}\n")
                                prev_volume = parsed[0][8:]
                            else:
                                sys.stdout.write(" \n")
                    else:
                        sys.stdout.write(" \n")


if __name__ == '__main__':
    loop = volume_watcher()
    loop.main()

