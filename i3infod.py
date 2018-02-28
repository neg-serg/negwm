#!/usr/bin/env python3
import socket
import i3ipc
from threading import Thread, Event


class BreakoutException(Exception):
    pass


class server_i3():
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.port = 31888
        self.name = ""
        self.ws_event = Event()
        self.ws_event.clear()

    def on_ws_focus(self, i3, event):
        self.name = event.current.name
        self.ws_event.set()

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind(('0.0.0.0', self.port))
        conn.listen(10)
        while True:
            try:
                current_conn, address = conn.accept()
                while True:
                    data = current_conn.recv(2048)
                    if data is None:
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'idle ws' in data.decode():
                        while True:
                            if self.ws_event.wait():
                                current_conn.shutdown(1)
                                current_conn.close()
                                self.ws_event.clear()
                                raise BreakoutException
                    elif 'ws' in data.decode():
                        current_conn.send(self.name.encode())
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
            except BreakoutException:
                pass


if __name__ == "__main__":
    srv = server_i3()
    Thread(target=srv.listen, daemon=True).start()
    Thread(
        target=srv.i3.main,
        daemon=False
    ).start()

