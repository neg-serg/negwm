import subprocess
import i3ipc
from singleton import Singleton
from cfg_master import CfgMaster
from time import sleep
from threading import Thread


class vol(Singleton, CfgMaster):
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.mpv_socket = "/tmp/mpv.socket"
        self.inc = 1
        self.mpd_addr = "127.0.0.1"
        self.mpd_port = "6600"
        self.mpd_status = "none"

        self.i3.on("window::focus", self.set_curr_win)
        self.default_cooldown = 4
        self.cooldown = self.default_cooldown

        Thread(
            target=self.update_mpd_status, args=(self.cooldown,), daemon=True
        ).start()

        self.current_win = self.i3.get_tree().find_focused()

    def set_curr_win(self, i3, event):
        self.current_win = event.container

    def switch(self, args) -> None:
        {
            "u": self.volume_up,
            "d": self.volume_down,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def check_mpd_status(self):
        p = subprocess.Popen(
            ['nc', self.mpd_addr, self.mpd_port],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        p.stdin.write(bytes('status\nclose\n', 'UTF-8'))
        p_com = p.communicate()[0].decode('UTF-8').split('\n')
        p.stdin.close()
        p.wait()

        if p_com is not None:
            ret = [t for t in p_com if 'state' in t]
            if ret and ret == ['state: play']:
                self.mpd_status = "play"

        if self.mpd_status != "play":
            self.mpd_status = "none"

    def update_mpd_status(self, cooldown):
        while True:
            self.check_mpd_status()
            sleep(cooldown)  # time to wait in sleep
            cooldown *= 2

    def get_mpd_status(self):
        return self.mpd_status

    def reload_config(self):
        self.__init__()

    def change_volume(self, val):
        self.cooldown = self.default_cooldown

        val_str = str(val)
        mpv_key = '9'
        if val > 0:
            val_str = "+" + str(val)
            mpv_key = '0'
        if self.get_mpd_status() == "play":
            p = subprocess.Popen(
                ['nc', f'{self.mpd_addr}', f'{self.mpd_port}'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            p.stdin.write(bytes(f'volume {val_str}\nclose\n', 'UTF-8'))
            p.communicate()[0].decode('UTF-8').split('\n')
            p.stdin.close()
        elif self.current_win.window_class == "mpv":
            p = subprocess.Popen(
                [
                    'xdotool', 'key',
                    '--window', str(self.current_win.window), mpv_key
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

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

