#!/usr/bin/python3

""" MPD info printing daemon.

This daemon prints current MPD volume like `tail -f` echo server, so there is
no need to use busy waiting to extract information from it.

Usage:
    ./polybar_mpd.py

Suppoused to be used inside polybar.

Config example:

[module/mpd]
type = custom/script
interval = 0
exec = PYTHONPATH=${XDG_CONFIG_HOME}/i3 python -u -m proc.polybar_mpd 2> /dev/null
exec-if = sleep 1
tail = true

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2020

"""

import asyncio
import sys
import time
from lib.standalone_cfg import modconfig


class polybar_mpd(modconfig):
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
        self.status_cmd_str = "currentsong\nstatus\n"

        # set string for the empty output
        if self.conf('show_volume').startswith('y'):
            self.empty_str = f"empty_y"
        else:
            self.empty_str = f"empty_non_y"

        # run mainloop
        self.main()

    def main(self):
        """ Mainloop starting here. """
        try:
            self.loop.run_until_complete(
                self.update_mpd_currentsong()
            )
        except ConnectionError:
            self.empty_output()
        finally:
            self.loop.close()

    def print_volume(self):
        """ Create nice and shiny output for polybar. """
        return f'volume'

    def empty_output(self):
        """ This output will be used if no information about volume. """
        sys.stdout.write(f'{self.empty_str}\n')

    def check_for_full(self):
        return not (self.conf("disable_on_full") and self.volume == "100")

    def pretty_printing(self, song_data):
        artist = song_data.get('Artist', '')
        title = song_data.get('Title', '')
        song_time = song_data.get('time', '')
        lhs = "%{F#005f87}〉%{F#005fd7}〉%{F#395573} %{F-}"
        delim = '%{F#395573}/%{F-}'
        if artist and title and song_time:
            sys.stdout.write(f'{lhs}{artist} ― {title} {song_time[0].strip()}{delim}{song_time[1].strip()}\n')

    async def initial_mpd_volume(self, reader, writer):
        data = await reader.read(self.buf_size)
        writer.write(self.status_cmd_str.encode(encoding='utf-8'))
        return data.startswith(b'OK')

    async def update_mpd_currentsong(self):
        """ Update MPD volume here and print it. """
        def time_convert(n):
            return time.strftime(
                " %M:%S", time.gmtime(n)
            ).replace(' 0', ' ')

        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port
        )
        if await self.initial_mpd_volume(reader, writer):
            while True:
                writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                stat_data = await reader.read(self.buf_size)
                ret = stat_data.decode('utf-8').split('\n')
                parsed = {}
                for tok in ret:
                    tok = tok.split(':')
                    for t in {'Artist', 'Title'}:
                        if tok[0] == t:
                            parsed[t] = tok[1].strip()
                    if tok[0] == 'time':
                        current_time = float(tok[1].strip())
                        all_time = float(tok[2].strip())
                        parsed['time'] = [time_convert(current_time), time_convert(all_time)]
                if parsed:
                    self.pretty_printing(parsed)
                await asyncio.sleep(1)


if __name__ == '__main__':
    polybar_mpd()
