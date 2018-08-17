#!/usr/bin/pypy3 -u

""" Volume printing daemon.

This daemon prints current MPD volume like `tail -f` echo server, so there is
no need to use busy waiting to extract information from it.

Usage:
    ./vol_printer.py

Suppoused to be used inside polybar.

Config example:

[module/volume]
type = custom/script
interval = 0
exec = ~/.config/i3/vol_printer.py
exec-if = sleep 1
tail = true

Also you need to use unbuffered output for polybar, otherwise you will see no
output at all. I've considered that pypy3 is better choise here, because of
this application run pretty long time to get advantages of JIT compilation.

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2018

"""

import asyncio
import os
import sys
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3")
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3/lib")
from basic_config import modconfig


class vol_printer(modconfig):
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        # Initialize modcfg.
        super().__init__(self.loop)

        # default MPD address
        self.addr = self.cfg.get("mpdaddr", "127.0.0.1")

        # default MPD port
        self.port = self.cfg.get("mpdport", "6600")

        # buffer size
        self.buf_size = self.cfg.get("bufsize", 1024)

        # output string
        self.volume = ""

        # command to wait for mixer or player events from MPD
        self.idle_mixer = "idle mixer player\n"

        # command to get status from MPD
        self.status_cmd_str = "status\n"

        # various MPD // Volume printer delimiters
        self.delimiter = self.cfg.get("delimiter", "||")

        # run mainloop
        self.main()

    def main(self):
        """ Mainloop starting here.
        """
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(
                self.update_mpd_volume(self.loop)
            )
        except ConnectionError:
            sys.stdout.write("\n")
            pass

    def print_volume(self):
        """ Create nice and shiny output for polybar.
        """
        return f'%{{F#395573}}{self.delimiter}%{{F-}}%{{F#cccccc}}' + \
            f'Vol: {self.volume}%%{{F-}}%{{F#395573}} ⟭%{{F-}}'

    def empty_output(self):
        """ This output will be used if no information about volume.
        """
        sys.stdout.write("%{{F#395573}} ⟭%{{F-}}\n")

    async def initial_mpd_volume(self, loop, reader, writer):
        """ Load MPD volume state when script started.
        """
        data = await reader.read(self.buf_size)
        writer.write(self.status_cmd_str.encode(encoding='utf-8'))
        stat_data = await reader.read(self.buf_size)
        parsed = stat_data.decode('utf-8').split('\n')
        if 'volume' in parsed[0]:
            self.volume = parsed[0][8:]
            if int(self.volume) >= 0:
                self.volume = self.print_volume()
                sys.stdout.write(f"{self.volume}\n")
            else:
                sys.stdout.write(f" \n")
        return data.startswith(b'OK')

    async def update_mpd_volume(self, loop):
        """ Update MPD volume here and print it.
        """
        prev_volume = 'wtf'
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port, loop=loop
        )
        if await self.initial_mpd_volume(loop, reader, writer):
            while True:
                writer.write(self.idle_mixer.encode(encoding='utf-8'))
                data = await reader.read(self.buf_size)
                if data.decode('utf-8'):
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.buf_size)
                    parsed = stat_data.decode('utf-8').split('\n')
                    if 'state: play' in parsed:
                        if 'volume' in parsed[0]:
                            self.volume = parsed[0][8:]
                            if int(self.volume) >= 0:
                                if prev_volume != self.volume:
                                    self.volume = self.print_volume()
                                    sys.stdout.write(f"{self.volume}\n")
                                prev_volume = parsed[0][8:]
                            else:
                                self.empty_output()
                    else:
                        prev_volume = 'wtf'
                        writer.close()
                        self.empty_output()
                        return
                else:
                    writer.close()
                    return


if __name__ == '__main__':
    loop = vol_printer()

