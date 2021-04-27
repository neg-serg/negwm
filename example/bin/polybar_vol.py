#!/usr/bin/python3

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
exec = PYTHONPATH=${XDG_CONFIG_HOME}/i3 python -u -m bin.polybar_vol 2> /dev/null
exec-if = sleep 1
tail = true

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2021

"""

import asyncio
import sys

from lib.standalone_cfg import modconfig


class polybar_vol(modconfig):
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        # Initialize modcfg.
        super().__init__()

        # default MPD address
        self.addr = str(self.conf("mpdaddr"))

        # default MPD port
        self.port = int(str(self.conf("mpdport")))

        # buffer size
        self.buf_size = int(str(self.conf("bufsize")))

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

        self.bracket_color = '#395573'
        self.bright_color = '#cccccc'
        self.foreground_color = '#cccccc'

        self.right_bracket = ""

        # set string for the empty output
        if str(self.conf('show_volume')).startswith('y'):
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
        asyncio.run(self.update_mpd_volume())

    def print_volume(self):
        """ Create nice and shiny output for polybar. """
        return f'%{{F{self.bracket_color}}}{self.delimiter}%{{F-}}' + \
            f'%{{F{self.foreground_color}}}' + \
            f'{self.vol_prefix}{self.volume}{self.vol_suffix}%{{F-}}' + \
            f'%{{F{self.bracket_color}}}{self.right_bracket}%{{F-}}'

    def empty_output(self):
        """ This output will be used if no information about volume. """
        sys.stdout.write(f'{self.empty_str}\n')

    def check_for_full(self):
        return not (self.conf("disable_on_full") and self.volume == "100")

    async def initial_mpd_volume(self, reader, writer):
        """ Load MPD volume state when script started. """
        mpd_stopped = None

        data = await reader.read(self.buf_size)
        writer.write(self.status_cmd_str.encode(encoding='utf-8'))
        stat_data = await reader.read(self.buf_size)
        parsed = stat_data.decode('utf-8').split('\n')
        if 'volume' in parsed[0]:
            self.volume = parsed[0][8:]
            if int(self.volume) >= 0 and self.check_for_full():
                self.volume = self.print_volume()
                sys.stdout.write(f"{self.volume}\n")
            else:
                sys.stdout.write("\n")
        else:
            for token in parsed:
                if token == 'state: stop':
                    mpd_stopped = True
                    break
            if mpd_stopped:
                sys.stdout.write("\n")
            else:
                print(self.empty_str)
        return data.startswith(b'OK')

    async def update_mpd_volume(self):
        """ Update MPD volume here and print it. """
        prev_volume = ''
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port
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
                            if not self.check_for_full():
                                sys.stdout.write("\n")
                            elif prev_volume != self.volume:
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
