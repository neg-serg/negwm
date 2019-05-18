""" Volume-manager daemon module.

This is a volume manager. Smart tool which allow you control volume of mpd, mpv
or whatever, depending on the context. For example if mpd playing it set
up/down the mpd volume, if it is not then it handles mpv volume via mpvc if mpv
window is not focused or via sending 0, 9 keyboard commands if it is.

"""
import subprocess
import socket
import asyncio
from cfg import cfg
from negi3mod import negi3mod


class vol(negi3mod, cfg):
    def __init__(self, i3, loop) -> None:
        """ Init function

        Args:
            i3: i3ipc connection
            loop: asyncio loop. It's need to be given as parameter because of
                  you need to bypass asyncio-loop to the thread
        """
        # Initialize cfg.
        cfg.__init__(self, i3, loop=loop)

        # i3ipc connection, bypassed by negi3mods runner.
        self.i3 = i3

        # Bypass loop from negi3mods script here.
        self.loop = loop

        # Default increment step for mpd.
        self.inc = self.conf("mpd_inc")

        # Default mpd address.
        self.mpd_addr = self.conf("mpd_addr")

        # Default mpd port.
        self.mpd_port = self.conf("mpd_port")

        # Default mpd buffer size.
        self.mpd_buf_size = self.conf("mpd_buf_size")

        # Default mpv socket.
        self.mpv_socket = self.conf("mpv_socket")

        # Send 0, 9 keys to the mpv window or not.
        self.use_mpv09 = self.conf("use_mpv09")

        # Cache current window on focus.
        self.i3.on("window::focus", self.set_curr_win)

        # Default mpd status is False
        self.mpd_playing = False

        # MPD idle command listens to the player events by default.
        self.idle_cmd_str = "idle player\n"

        # MPD status string, which we need send to extract most of information.
        self.status_cmd_str = "status\n"

        self.bindings = {
            "u": self.volume_up,
            "d": self.volume_down,
            "reload": self.reload_config,
        }

        # Initial state for the current_win
        self.current_win = self.i3.get_tree().find_focused()

        # Setup asyncio, because of it is used in another thread.
        asyncio.set_event_loop(self.loop)
        asyncio.ensure_future(self.update_mpd_status(self.loop))

    def set_curr_win(self, i3, event) -> None:
        """ Cache the current window.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        self.current_win = event.container

    async def update_mpd_status(self, loop) -> None:
        """ Asynchronous function to get current MPD status.

            Args:
                loop: asyncio.loop
        """
        reader, writer = await asyncio.open_connection(
            host=self.mpd_addr, port=self.mpd_port, loop=loop
        )
        data = await reader.read(self.mpd_buf_size)
        if data.startswith(b'OK'):
            writer.write(self.status_cmd_str.encode(encoding='utf-8'))
            stat_data = await reader.read(self.mpd_buf_size)
            if 'state: play' in stat_data.decode('UTF-8').split('\n'):
                self.mpd_playing = True
            else:
                self.mpd_playing = False
            while True:
                writer.write(self.idle_cmd_str.encode(encoding='utf-8'))
                data = await reader.read(self.mpd_buf_size)
                if 'player' in data.decode('UTF-8').split('\n')[0]:
                    writer.write(self.status_cmd_str.encode(encoding='utf-8'))
                    stat_data = await reader.read(self.mpd_buf_size)
                    if 'state: play' in stat_data.decode('UTF-8').split('\n'):
                        self.mpd_playing = True
                    else:
                        self.mpd_playing = False
                else:
                    self.mpd_playing = False
                if writer.transport._conn_lost:
                    # TODO: add function to wait for MPD port here.
                    break

    def change_volume(self, val: int) -> None:
        """ Change volume here.

            This function using MPD state information, information about
            currently focused window from i3, etc to perform contextual volume
            changing.

            Args:
                val (int): volume step.
        """
        val_str = str(val)
        mpv_key = '9'
        mpv_cmd = '--decrease'
        if val > 0:
            val_str = "+" + str(val)
            mpv_key = '0'
            mpv_cmd = '--increase'
        if self.mpd_playing:
            self.mpd_socket = socket.socket(
                socket.AF_INET6, socket.SOCK_STREAM
            )
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

    def volume_up(self, *args) -> None:
        """ Increase target volume level.

            Args:
                args (*args): used as multiplexer for volume changing because
                              of pipe-based nature of negi3mods IPC.
        """
        count = len(args)
        if count <= 0:
            count = 1
        self.change_volume(count)

    def volume_down(self, *args) -> None:
        """ Decrease target volume level.

            Args:
                args (*args): used as multiplexer for volume changing because
                              of pipe-based nature of negi3mods IPC.
        """
        count = len(args)
        if count <= 0:
            count = 1
        self.change_volume(-count)

