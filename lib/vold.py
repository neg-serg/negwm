import subprocess
import socket
import asyncio
from singleton import Singleton
from modi3cfg import modi3cfg


class vol(Singleton, modi3cfg):
    def __init__(self, i3, loop):
        super().__init__(i3, loop)
        self.i3 = i3
        self.loop = loop
        self.inc = self.cfg.get("mpd_inc", 1)
        self.mpd_addr = self.cfg.get("mpd_addr", "127.0.0.1")
        self.mpd_port = self.cfg.get("mpd_port", "6600")
        self.mpv_socket = self.cfg.get("mpv_socket", "/tmp/mpv.socket")
        self.mpd_buf_size = self.cfg.get("mpd_buf_size", 1024)
        self.use_mpv09 = self.cfg.get("use_mpv09", True)
        self.i3.on("window::focus", self.set_curr_win)

        self.mpd_status = "none"
        self.idle_cmd_str = "idle player\n"
        self.status_cmd_str = "status\n"

        self.current_win = self.i3.get_tree().find_focused()

        asyncio.set_event_loop(self.loop)
        asyncio.ensure_future(self.update_mpd_status(self.loop))

    def set_curr_win(self, i3, event):
        self.current_win = event.container

    async def update_mpd_status(self, loop):
        reader, writer = await asyncio.open_connection(
            host=self.mpd_addr, port=self.mpd_port, loop=loop
        )
        data = await reader.read(self.mpd_buf_size)
        if data.startswith(b'OK'):
            writer.write(self.status_cmd_str.encode(encoding='utf-8'))
            stat_data = await reader.read(self.mpd_buf_size)
            if 'state: play' in stat_data.decode('UTF-8').split('\n'):
                self.mpd_status = "play"
            else:
                self.mpd_status = "none"
            while True:
                writer.write(self.idle_cmd_str.encode(encoding='utf-8'))
                data = await reader.read(self.mpd_buf_size)
                if 'player' in data.decode('UTF-8').split('\n')[0]:
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.mpd_buf_size)
                    if 'state: play' in stat_data.decode('UTF-8').split('\n'):
                        self.mpd_status = "play"
                    else:
                        self.mpd_status = "none"

    def switch(self, args) -> None:
        {
            "u": self.volume_up,
            "d": self.volume_down,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def change_volume(self, val):
        val_str = str(val)
        mpv_key = '9'
        mpv_cmd = '--decrease'
        if val > 0:
            val_str = "+" + str(val)
            mpv_key = '0'
            mpv_cmd = '--increase'
        if self.mpd_status == "play":
            self.mpd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.mpd_socket.connect((self.mpd_addr, int(self.mpd_port)))
                self.mpd_socket.send(bytes(
                        f'volume {val_str}\nclose\n', 'UTF-8'
                ))
                self.mpd_socket.recv(self.mpd_buf_size)
            finally:
                self.mpd_socket.close()
        elif self.use_mpv09 and self.current_win.window_class == "mpv":
            subprocess.run([
                    'xdotool', 'type', '--clearmodifiers',
                    '--delay', '0', str(mpv_key) * abs(val)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif self.use_mpv09:
            subprocess.run([
                    'mpvc', 'set', 'volume', mpv_cmd, str(abs(val))
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            return

    def volume_up(self, *args):
        count = len(args)
        if count <= 0:
            count = 1
        self.change_volume(count)

    def volume_down(self, *args):
        count = len(args)
        if count <= 0:
            count = 1
        self.change_volume(-count)

