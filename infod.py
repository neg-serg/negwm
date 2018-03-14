#!/usr/bin/pypy3

import socket
import lib.i3ipc as i3ipc
from lib.singleton import Singleton
from modi3cfg import modi3cfg
from threading import Thread

from nsd import ns
from circled import circle


class info(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3):
        super().__init__(i3)
        self.i3 = i3

        self.addr = self.cfg.get("addr", '0.0.0.0')
        self.port = int(self.cfg.get("port", '31888'))
        self.conn_count = int(self.cfg.get("conn_count", 10))
        self.buf_size = int(self.cfg.get('buf_size', 2048))

        self.ns_instance = ns(self.i3)
        self.circle_instance = circle(self.i3)

    def close_conn(self):
        self.curr_conn.shutdown(1)
        self.curr_conn.close()

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.addr, self.port))
        conn.listen(self.conn_count)

        while True:
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


if __name__ == '__main__':
    i3 = i3ipc.Connection()
    loop = info(i3)
    Thread(target=loop.listen, daemon=True).start()
    loop.i3.main()

