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

        self.addr = self.cfg.get("addr", '0.0.0.0')
        self.port = int(self.cfg.get("port", '31888'))
        self.conn_count = int(self.cfg.get("conn_count", 10))

        self.buf_size = int(self.cfg.get('buf_size', 2048))
        self.binding_mode = ""
        self.mode_regex = re.compile('.*mode ')
        self.split_by = re.compile('[;,]')

        self.ns_instance = ns(self.i3, self.loop)
        self.circle_instance = circle(self.i3, self.loop)
        self.vol_instance = vol(self.i3, self.loop)

    def switch(self, args):
        {
            "request": self.request,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

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
            except BreakoutException:
                pass

