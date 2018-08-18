#!/usr/bin/pypy3

""" This is an application which supposed to be run separately from negi3mods.

This application can extract some info about negi3mod state and return it as
echo server. It is very simple, but fast enough. Maybe I will improve this code
with asyncio or something like this in the future.

"""

import socket
import i3ipc
from threading import Thread
import os
import sys
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3")
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3/lib")
from singleton import Singleton
from modi3cfg import modi3cfg
from ns import ns
from circle import circle


class info(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3):
        """ Init function

        Args:
            i3: i3ipc connection.
        """

        # modi3cfg init.
        super().__init__(i3)

        # server addresses.
        self.echo_addr = self.cfg.get("echo_addr", '::')
        self.wait_proc_addr = self.cfg.get("wait_proc_addr", '::')

        # server ports.
        self.echo_port = int(self.cfg.get("echo_port", '31888'))
        self.wait_proc_port = int(self.cfg.get("wait_port", '31887'))

        # default connection count.
        self.conn_count = int(self.cfg.get("conn_count", 10))

        # buffer size.
        self.buf_size = int(self.cfg.get('buf_size', 2048))

        # nsd instance. We need it to extract info
        # circled instance. We need it to extract info
        self.ns_instance = ns(i3)
        self.circle_instance = circle(i3)

    def close_conn(self, curr_conn):
        """ Close connection.

            This function is just for DRY principle and convinience.
        """
        curr_conn.shutdown(1)
        curr_conn.close()

    def echo_mainloop(self):
        """ Echo server mainloop, listen to request, returns echo, very stupid.
        """
        conn = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.echo_addr, self.echo_port))
        conn.listen(self.conn_count)

        while True:
            curr_conn, _ = conn.accept()
            while True:
                data = curr_conn.recv(self.buf_size)
                if data is None:
                    self.close_conn(curr_conn)
                    break
                elif 'ns_list' in data.decode():
                    output = [k for k in self.ns_instance.cfg]
                    curr_conn.send(bytes(str(output), 'UTF-8'))
                    self.close_conn(curr_conn)
                    break
                elif 'circle_list' in data.decode():
                    output = [k for k in self.circle_instance.cfg]
                    curr_conn.send(bytes(str(output), 'UTF-8'))
                    self.close_conn(curr_conn)
                    break

    def wait_proc_mainloop(self):
        """ Wait proc mainloop, listen to request, parse it, returns echo when
            done.
        """
        conn = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.wait_proc_addr, self.wait_proc_port))
        conn.listen(self.conn_count)

        while True:
            curr_conn, _ = conn.accept()
            while True:
                data = curr_conn.recv(self.buf_size)
                if data is None:
                    self.close_conn(curr_conn)
                    break
                elif 'wait_for' in data.decode():
                    print(data.decode())
                    curr_conn.send(bytes(str(data.decode()), 'UTF-8'))
                    self.close_conn(curr_conn)
                    break


if __name__ == '__main__':
    i3 = i3ipc.Connection()
    proc = info(i3)
    Thread(target=proc.echo_mainloop, daemon=True).start()
    Thread(target=proc.wait_proc_mainloop, daemon=True).start()
    proc.i3.main()

