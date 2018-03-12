#!/usr/bin/pypy3

import i3ipc
import socket
from threading import Thread, Event


class BreakoutException(Exception):
    pass


class idle_ws():
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.event = Event()
        self.event.set()
        self.i3.on('workspace::focus', self.on_ws_focus)

    def on_ws_focus(self, i3, event):
        self.event.set()

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind(('0.0.0.0', 31889))
        conn.listen(10)

        while True:
            try:
                curr_conn, _ = conn.accept()
                while True:
                    data = curr_conn.recv(1024)
                    if data is None:
                        curr_conn.shutdown(1)
                        curr_conn.close()
                        break
                    elif 'idle' in data.decode():
                        while self.event.wait():
                            self.event.clear()
                            curr_conn.send(bytes(str(''), 'UTF-8'))
                            curr_conn.shutdown(1)
                            curr_conn.close()
                            raise BreakoutException
            except BreakoutException:
                pass


if __name__ == '__main__':
    loop = idle_ws()
    Thread(target=loop.listen, daemon=True).start()
    loop.i3.main()

