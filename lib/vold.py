import subprocess
import i3ipc
import shlex
from singleton import Singleton
from cfg_master import CfgMaster


class vol(Singleton, CfgMaster):
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.mpv_socket = "/tmp/mpv.socket"
        self.inc = 1
        self.mpd_status = ""
        self.mpd_addr = "127.0.0.1"
        self.mpd_port = "6600"

        self.i3.on("window::focus", self.set_curr_win)

        self.current_win = self.i3.get_tree().find_focused()

    def set_curr_win(self, i3, event):
        self.current_win = event.container

    def switch(self, args) -> None:
        {
            "u": self.volume_up,
            "d": self.volume_down,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def get_mpd_status(self):
        p = subprocess.Popen(
            shlex.split(f"nc {self.mpd_addr} {self.mpd_port}"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        p.stdin.write(bytes(f'status\nclose\n', 'UTF-8'))
        p_com = p.communicate()[0].decode('UTF-8').split('\n')
        p.stdin.close()
        p.wait()
        if p_com is not None:
            ret = [t for t in p_com if 'state' in t]
            if ret and ret == ['state: play']:
                return "play"
        return "none"

    def reload_config(self):
        self.__init__()

    def volume_up(self, *args):
        count = len(args)
        if count <= 0:
            count = 1
        if self.get_mpd_status() == "play":
            p = subprocess.Popen(
                shlex.split(f"nc {self.mpd_addr} {self.mpd_port}"),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            p.stdin.write(bytes(f'volume +{count}\nclose\n', 'UTF-8'))
            p.communicate()[0].decode('UTF-8').split('\n')
            p.stdin.close()
        elif self.current_win.window_class == "mpv":
            p = subprocess.Popen(
                shlex.split(
                    f'xdotool key --window {self.current_win.id} 0'
                ),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

    def volume_down(self, *args):
        count = len(args)
        if count <= 0:
            count = 1
        if self.get_mpd_status() == "play":
            p = subprocess.Popen(
                shlex.split(f"nc {self.mpd_addr} {self.mpd_port}"),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            p.stdin.write(bytes(f'volume -{count}\nclose\n', 'UTF-8'))
            p.communicate()[0].decode('UTF-8').split('\n')
            p.stdin.close()
        elif self.current_win.window_class == "mpv":
            p = subprocess.Popen(
                shlex.split(
                    f'xdotool key --window {self.current_win.id} 9'
                ),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

