import subprocess
import re
import socket
from singleton import Singleton
from cfg_master import CfgMaster

from nsd import ns
from circled import circle
from vold import vol


class BreakoutException(Exception):
    pass


class info(CfgMaster):
    __metaclass__ = Singleton

    def __init__(self, i3, loop):
        super().__init__(i3)
        self.i3 = i3
        self.loop = loop
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.i3.on('binding', self.on_eventent)

        self.addr = self.cfg.get("addr", '0.0.0.0')
        self.port = int(self.cfg.get("port", '31888'))
        self.conn_count = int(self.cfg.get("conn_count", 10))

        self.ws_color = self.cfg.get('workspace_color', "#8FA8C7")
        self.buf_size = int(self.cfg.get('buf_size', 2048))
        self.ws_name = ""
        self.binding_mode = ""
        self.mode_regex = re.compile('.*mode ')
        self.split_by = re.compile('[;,]')

        self.ns_instance = ns(self.i3, self.loop)
        self.circle_instance = circle(self.i3, self.loop)
        self.vol_instance = vol(self.i3, self.loop)

        for ws in self.i3.get_workspaces():
            if ws.focused:
                self.ws_name = ws.name
                if not self.ws_name[0].isalpha():
                    self.ws_name = self.colorize(
                        self.ws_name[0], color=self.ws_color
                    ) + self.ws_name[1:]
                break

    def switch(self, args):
        {
            "request": self.request,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def on_ws_focus(self, i3, event):
        self.ws_name = event.current.name
        if not self.ws_name[0].isalpha():
            self.ws_name = self.colorize(
                self.ws_name[0], color="#8FA8C7"
            ) + self.ws_name[1:]

    def colorize(self, s, color="#005fd7"):
        return f"%{{F{color}}}{s}%{{F#ccc}}"

    def on_eventent(self, i3, event):
        bind_cmd = event.binding.command
        for t in re.split(self.split_by, bind_cmd):
            if 'mode' in t:
                ret = re.sub(self.mode_regex, '', t)
                if ret[0] == ret[-1] and ret[0] in {'"', "'"}:
                    ret = ret[1:-1]
                    if ret == "default":
                        self.binding_mode = ''
                    else:
                        self.binding_mode = self.colorize(ret) + ' '

    def close_conn(self):
        self.curr_conn.shutdown(1)
        self.curr_conn.close()

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.addr, self.port))
        conn.listen(self.conn_count)

        while True:
            try:
                self.curr_conn, _ = conn.accept()
                while True:
                    data = self.curr_conn.recv(self.buf_size)
                    if data is None:
                        self.close_conn()
                        break
                    elif 'ws' in data.decode():
                        self.curr_conn.send((self.binding_mode + self.ws_name).encode())
                        self.close_conn()
                        break
                    elif 'ns_list' in data.decode():
                        output = [k for k in self.ns_instance.cfg]
                        self.curr_conn.send(bytes(str(output), 'UTF-8'))
                        self.close_conn()
                        break
                    elif 'circle_list' in data.decode():
                        output = [k for k in self.circle_instance.cfg]
                        self.curr_conn.send(bytes(str(output), 'UTF-8'))
                        self.close_conn()
                        break
                    elif 'v' in data.decode():
                        output = self.vol_instance.volume
                        self.curr_conn.send(bytes(str(output), 'UTF-8'))
                        self.close_conn()
                        break
            except BreakoutException:
                pass

