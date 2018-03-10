import subprocess
import socket
from threading import Thread, Event
from singleton import Singleton
from cfg_master import CfgMaster


class vol(Singleton, CfgMaster):
    def __init__(self, i3):
        super().__init__(i3)
        self.i3 = i3

        self.inc = self.cfg.get("mpd_inc", 1)
        self.mpd_addr = self.cfg.get("mpd_addr", "127.0.0.1")
        self.mpd_port = self.cfg.get("mpd_port", "6600")
        self.mpv_socket = self.cfg.get("mpv_socket", "/tmp/mpv.socket")
        self.use_mpv09 = self.cfg.get("use_mpv09", True)

        self.i3.on("window::focus", self.set_curr_win)
        self.player_event = Event()

        self.mpd_status = "none"

        Thread(target=self.update_mpd_status, daemon=True).start()
        Thread(target=self.wait_for_mpd_status_update, daemon=True).start()

        self.player_event.set()
        self.current_win = self.i3.get_tree().find_focused()

    def set_curr_win(self, i3, event):
        self.current_win = event.container

    def switch(self, args) -> None:
        {
            "u": self.volume_up,
            "d": self.volume_down,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def wait_for_mpd_status_update(self):
        while True:
            p = subprocess.Popen(
                ['mpc', 'idleloop', 'player'],
                stdout=subprocess.PIPE
            )
            (out, _) = p.communicate()
            # Read mpc idleloop for player event
            while True:
                if not out and p.poll() is not None:
                    self.player_event.clear()
                    break
                if out:
                    self.mpd_status = "none"
                    self.player_event.set()
            p.kill()

    def check_mpd_status(self):
        out = subprocess.run(
            ['nc', self.mpd_addr, self.mpd_port],
            stdout=subprocess.PIPE,
            input=bytes('status\nclose\n', 'UTF-8')
        ).stdout

        if out is not None:
            out = out.decode('UTF-8').split('\n')
            ret = [t for t in out if 'state' in t]
            if ret == ['state: play']:
                self.mpd_status = "play"

        if self.mpd_status != "play":
            self.mpd_status = "none"

    def update_mpd_status(self):
        while True:
            if self.player_event.wait():
                self.check_mpd_status()
                self.player_event.clear()

    def reload_config(self):
        self.__init__(self.i3)

    def change_volume(self, val):
        val_str = str(val)
        mpv_key = '9'
        mpv_cmd = '--decrease'
        if val > 0:
            val_str = "+" + str(val)
            mpv_key = '0'
            mpv_cmd = '--increase'
        if self.mpd_status == "play":
            self.mpd_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            self.mpd_socket.connect((self.mpd_addr, int(self.mpd_port)))
            self.mpd_socket.send(bytes(f'volume {val_str}\nclose\n', 'UTF-8'))
            self.mpd_socket.recv(1024)
            self.mpd_socket.close()
        elif self.use_mpv09 and self.current_win.window_class == "mpv":
            subprocess.run([
                'xdotool', 'type', '--clearmodifiers',
                '--delay', '0', str(mpv_key) * abs(val)
            ])
        elif self.use_mpv09:
            subprocess.run([
                'mpvc', 'set', 'volume', mpv_cmd, str(abs(val))
            ])
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

