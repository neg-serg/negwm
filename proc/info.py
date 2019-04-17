#!/usr/bin/pypy3

""" This is an application which supposed to be run separately from negi3mods.

This application can extract some info about negi3mod state and return it as
echo server. It is very simple, but fast enough. Maybe I will improve this code
with asyncio or something like this in the future.

"""

import socket
import i3ipc
from threading import Thread
import subprocess
import shlex
import collections

from lib.locker import get_lock
from lib.singleton import Singleton
from lib.modi3cfg import modi3cfg
from lib.ns import ns
from lib.circle import circle


class info(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3):
        """ Init function

        Args:
            i3: i3ipc connection.
        """

        # modi3cfg init.
        modi3cfg.__init__(self, i3)

        # server addresses.
        self.echo_addr = self.conf("echo_addr")
        self.wait_proc_addr = self.conf("wait_proc_addr")

        # server ports.
        self.echo_port = int(self.conf("echo_port"))
        self.wait_proc_port = int(self.conf("wait_port"))

        # default connection count.
        self.conn_count = int(self.conf("conn_count"))

        # buffer size.
        self.buf_size = int(self.conf('buf_size'))

        # nsd instance. We need it to extract info
        # circled instance. We need it to extract info
        self.ns_instance = ns(i3)
        self.circle_instance = circle(i3)

        self.exec_wait_queue = collections.deque(maxlen=10)
        self.created_wins = collections.deque(maxlen=10)

        self.need_check = False

        i3.on('window::new', self.wait_for_window)

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
                    wattr = self.parse_exec_wait(data.decode())
                    self.exec_wait = self.await_for_window(wattr, curr_conn)
                    next(self.exec_wait)
                    break

    def await_for_window(self, wattr, curr_conn):
        ans = 'win_not_created'
        if wattr is not None:
            while not self.need_check:
                yield
            self.need_check = False
            del_w = None
            for w in self.created_wins:
                if wattr == w:
                    ans = 'win_created'
                    del_w = w
                    break
                else:
                    continue
        if del_w is not None:
            self.created_wins.remove(del_w)
        curr_conn.send(bytes(ans, 'UTF-8'))
        self.close_conn(curr_conn)
        yield None

    def parse_exec_wait(self, wait_cmd):
        wattr = {'class': "", 'instance': "", 'name': "", 'exec': ""}
        wait_cmd_split = shlex.split(wait_cmd)
        for tok in wait_cmd_split[1:]:
            if len(tok):
                if 'class=' in tok:
                    wattr['class'] = tok.split('class=')[1]
                elif 'instance=' in tok:
                    wattr['instance'] = tok.split('instance=')[1]
                elif 'name=' in tok:
                    wattr['name'] = tok.split('name=')[1]
                else:
                    wattr['exec'] = tok

        if wattr['exec']:
            if wattr['class'] or wattr['instance'] or wattr['name']:
                self.exec_wait_queue.appendleft(wattr)
                try:
                    subprocess.Popen(
                        shlex.split(wattr['exec']),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass

        return wattr

    def wait_for_window(self, i3, event):
        win = event.container
        self.winlist = i3.get_tree()
        tgt_wattr = None
        for wattr in self.exec_wait_queue:
            if wattr['class'] and win.window_class != wattr['class'] or \
                wattr['instance'] and win.window_instance != wattr['instance'] or \
                    wattr['name'] and win.window_instance != wattr['name']:
                        continue
            else:
                self.created_wins.append(wattr)
                self.need_check = True
                self.exec_wait.send(True)
                tgt_wattr = wattr
                break
        if tgt_wattr is not None:
            self.exec_wait_queue.remove(tgt_wattr)


if __name__ == '__main__':
    get_lock(__file__)
    i3 = i3ipc.Connection()
    proc = info(i3)
    Thread(target=proc.echo_mainloop, daemon=True).start()
    Thread(target=proc.wait_proc_mainloop, daemon=True).start()
    proc.i3.main()

