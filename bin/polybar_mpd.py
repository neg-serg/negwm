#!/usr/bin/python3 -u

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
from functools import update_wrapper
import sys
import time
from lib.standalone_cfg import modconfig


class polybar_mpd(modconfig):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        modconfig.__init__(self)

        # default MPD address
        self.addr = self.conf("mpdaddr")
        # default MPD port
        self.port = self.conf("mpdport")
        # buffer size
        self.buf_size = self.conf("bufsize")

        # command to wait for mixer or player events from MPD
        self.idle_player = "idle player\n"

        # command to get song status from MPD
        self.get_song_data_cmd = "currentsong\nstatus\n"

        # run mainloop
        self.main()

    def main(self):
        """ Mainloop starting here. """
        try:
            self.loop.run_until_complete(
                self.current_song_loop()
            )
        except ConnectionError:
            sys.stdout.write(f'\n')
        finally:
            self.loop.close()

    def pretty_printing(self, song_data):
        artist = song_data.get('Artist', '')
        title = song_data.get('Title', '')
        song_time = song_data.get('time', '')
        lhs = "%{F#005f87}〉%{F#005fd7}〉%{F#395573} %{F-}"
        delim = '%{F#395573}/%{F-}'
        if artist and title and song_time:
            sys.stdout.write(f'{lhs}{artist} ― {title} ' \
                f'{song_time[0].strip()}{delim}{song_time[1].strip()}\n')

    def time_convert(self, n):
        return time.strftime(
            " %M:%S", time.gmtime(n)
        ).replace(' 0', ' ')

    async def update_mpd_stat(self, reader, writer):
        writer.write(self.get_song_data_cmd.encode(encoding='utf-8'))
        raw_song_data = await reader.read(self.buf_size)
        ret = raw_song_data.decode('utf-8').split('\n')
        song_data = {}
        for tok in ret:
            tok = tok.split(':', maxsplit=1)
            for t in {'Artist', 'Title', 'time', 'state'}:
                if tok[0] == t:
                    song_data[t] = tok[1].strip()
                    if tok[0] == 'time':
                        t = tok[1].split(':')
                        current_time = float(t[0].strip())
                        total_time = float(t[1].strip())
                        song_data['time'] = [
                            self.time_convert(current_time),
                            self.time_convert(total_time)
                        ]
        return song_data

    async def mpd_stat_at_start(self, reader, writer):
        data = await reader.read(self.buf_size)
        writer.write(self.get_song_data_cmd.encode(encoding='utf-8'))
        return data.startswith(b'OK')

    async def current_song_loop(self):
        """ Update MPD volume here and print it. """
        reader, writer = await asyncio.open_connection(
            host=self.addr, port=self.port
        )
        if await self.mpd_stat_at_start(reader, writer):
            while True:
                song_data = await self.update_mpd_stat(reader, writer)
                if song_data.get('state', '') == 'play':
                    self.pretty_printing(song_data)
                else:
                    sys.stdout.write('\n')
                await asyncio.sleep(0.1)


if __name__ == '__main__':
    polybar_mpd()
