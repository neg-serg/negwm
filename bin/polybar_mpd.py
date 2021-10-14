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
exec = PYTHONPATH=${XDG_CONFIG_HOME}/negi3wm python -u -m bin.polybar_mpd 2> /dev/null
exec-if = sleep 1
tail = true

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2021

"""

import asyncio
import sys
import time

class polybar_mpd():
    addr = '::1'
    port = '6600'
    buf_size = 2048
    fg = '%{F#ffCFCFDB}'
    hi_color = '%{F#395573}'
    wave = '%{T4} %{T-}'
    fg_end = "%{F-}"
    time_color = '%{F#ffCFCFDB}'
    delim = '%{F#657491}―%{F}'

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        super().__init__()
        # command to wait for mixer or player events from MPD
        self.idle_player = "idle player\n"
        # command to get song status from MPD
        self.get_song_data_cmd = "currentsong\nstatus\n"
        self.main()

    def main(self):
        """ Mainloop starting here. """
        asyncio.run(self.current_song_loop())

    @staticmethod
    def pretty_printing(song_data):
        artist = f"{polybar_mpd.fg}{song_data.get('Artist', '')}"
        title = f"{polybar_mpd.fg}{song_data.get('Title', '')}"
        t = song_data.get('time', '')
        lhs = f"{polybar_mpd.hi_color} {polybar_mpd.wave}{polybar_mpd.fg_end}"
        delim = f"{polybar_mpd.hi_color}/{polybar_mpd.fg_end}"
        if artist and title and t:
            duration = f'%{{T5}}{polybar_mpd.time_color}{t[0].strip()}{delim}{polybar_mpd.time_color}{t[1].strip()}%{{T-}}\n'
            sys.stdout.write(f'{lhs}{artist} {polybar_mpd.delim} {title} {duration}')

    @staticmethod
    def time_convert(n):
        return time.strftime(" %M:%S", time.gmtime(n)).replace(' 0', ' ')

    async def update_mpd_stat(self, reader, writer):
        writer.write(self.get_song_data_cmd.encode(encoding='utf-8'))
        raw_song_data = await reader.read(polybar_mpd.buf_size)
        ret = raw_song_data.decode('utf-8').split('\n')
        song_data = {}
        for tok in ret:
            tok = tok.split(':', maxsplit=1)
            for t in ['Artist', 'Title', 'time', 'state']:
                if tok[0] == t:
                    song_data[t] = tok[1].strip()
                    if tok[0] == 'time':
                        t = tok[1].split(':')
                        current_time = float(t[0].strip())
                        total_time = float(t[1].strip())
                        song_data['time'] = [
                            polybar_mpd.time_convert(current_time),
                            polybar_mpd.time_convert(total_time)
                        ]
        return song_data

    async def mpd_stat_at_start(self, reader, writer):
        data = await reader.read(self.buf_size)
        writer.write(self.get_song_data_cmd.encode(encoding='utf-8'))
        return data.startswith(b'OK')

    async def current_song_loop(self):
        """ Update MPD volume here and print it. """
        reader, writer = await asyncio.open_connection(
            host=polybar_mpd.addr, port=polybar_mpd.port
        )
        if await self.mpd_stat_at_start(reader, writer):
            while True:
                song_data = await self.update_mpd_stat(reader, writer)
                if song_data.get('state', '') == 'play':
                    polybar_mpd.pretty_printing(song_data)
                else:
                    sys.stdout.write('\n')
                await asyncio.sleep(0.1)

if __name__ == '__main__':
    polybar_mpd()
