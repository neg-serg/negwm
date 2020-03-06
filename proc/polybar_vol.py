#!/usr/bin/pypy3 -u

""" Volume printing daemon.

This daemon prints current MPD volume like `tail -f` echo server, so there is
no need to use busy waiting to extract information from it.

Usage:
    ./polybar_vol.py

Suppoused to be used inside polybar.

Config example:

[module/volume]
type = custom/script
interval = 0
exec = ~/.config/i3/proc/polybar_vol.py
exec-if = sleep 1
tail = true

Also you need to use unbuffered output for polybar, otherwise you will see no
output at all. I've considered that pypy3 is better choise here, because of
this application run pretty long time to get advantages of JIT compilation.

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2020

"""

import asyncio
import sys

from lib.standalone_cfg import modconfig
from lib.misc import Misc


class polybar_vol(modconfig):
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        # Initialize modcfg.
        modconfig.__init__(self)

        # default MPD address
        self.addr = self.conf("mpdaddr")

        # default MPD port
        self.port = self.conf("mpdport")

        # buffer size
        self.buf_size = self.conf("bufsize")

        # output string
        self.volume = ""

        # command to wait for mixer or player events from MPD
        self.idle_mixer = "idle mixer player\n"

        # command to get status from MPD
        self.status_cmd_str = "status\n"

        # various MPD // Volume printer delimiters
        self.delimiter = self.conf("delimiter")

        # volume prefix and suffix
        self.vol_prefix = self.conf("vol_prefix")
        self.vol_suffix = self.conf("vol_suffix")

        # xrdb-colors: use blue by default for brackets
        self.bracket_color_field = self.conf("bracket_color_field")
        self.bright_color_field = self.conf("bright_color_field")
        self.foreground_color_field = self.conf("foreground_color_field")

        self.bracket_color = Misc.extract_xrdb_value(self.bracket_color_field)
        self.bright_color = Misc.extract_xrdb_value(self.bright_color_field)
        self.foreground_color = Misc.extract_xrdb_value(
            self.foreground_color_field
        )

        self.right_bracket = ""

        # set string for the empty output
        if self.conf('show_volume').startswith('y'):
            self.empty_str = f"%{{F{self.bracket_color}}}{self.delimiter}" + \
                f"%{{F{self.bright_color}}}" + \
                f"{self.vol_prefix}%{{F{self.foreground_color}}}n/a%{{F-}}" + \
                f" %{{F{self.bracket_color}}}{self.right_bracket}%{{F-}}"
        else:
            self.empty_str = f" %{{F{self.bracket_color}}}" + \
                f"{self.right_bracket}%{{F-}}"

        # run mainloop
        self.main()

    def main(self):
        """ Mainloop starting here. """
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(
                self.update_mpd_volume(self.loop)
            )
        except ConnectionError:
            self.empty_output()
        finally:
            self.loop.close()

    def print_volume(self):
        """ Create nice and shiny output for polybar. """
        return f'%{{F{self.bracket_color}}}{self.delimiter}%{{F-}}' + \
            f'%{{F{self.foreground_color}}}' + \
            f'{self.vol_prefix}{self.volume}{self.vol_suffix}%{{F-}}' + \
            f'%{{F{self.bracket_color}}}{self.right_bracket}%{{F-}}'

    def empty_output(self):
        """ This output will be used if no information about volume. """
        sys.stdout.write(f'{self.empty_str}\n')

    async def initial_mpd_volume(self, reader, writer):
        """ Load MPD volume state when script started. """
        mpd_stopped = None

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
        else:
            for token in parsed:
                if token == 'state: stop':
                    mpd_stopped = True
                    break
            if mpd_stopped:
                print()
            else:
                print(self.empty_str)
        return data.startswith(b'OK')

    async def update_mpd_volume(self, loop):
        """ Update MPD volume here and print it. """
        prev_volume = ''
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port, loop=loop
        )
        if await self.initial_mpd_volume(reader, writer):
            while True:
                writer.write(self.idle_mixer.encode(encoding='utf-8'))
                data = await reader.read(self.buf_size)
                if data.decode('utf-8'):
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.buf_size)
                    parsed = stat_data.decode('utf-8').split('\n')
                    if 'state: play' in parsed and 'volume' in parsed[0]:
                        self.volume = parsed[0][8:]
                        if int(self.volume) >= 0:
                            if prev_volume != self.volume:
                                self.volume = self.print_volume()
                                sys.stdout.write(f"{self.volume}\n")
                            prev_volume = parsed[0][8:]
                    else:
                        prev_volume = ''
                        writer.close()
                        self.empty_output()
                        return
                else:
                    prev_volume = ''
                    writer.close()
                    self.empty_output()
                    return


if __name__ == '__main__':
    polybar_vol()
