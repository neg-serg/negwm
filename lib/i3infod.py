#!/usr/bin/env python3
import socket
import i3ipc
import nsd

from threading import Thread, Event


class BreakoutException(Exception):
    pass


class i3info():
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.addr = '0.0.0.0'
        self.port = 31888
        self.name = ""
        self.ws_event = Event()
        self.ws_event.clear()
        self.req_event = Event()
        self.req_event.clear()

    def switch(self, args):
        {

            "ns_list": self.ns_list,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def ns_list(self):
        self.req_event.set()

    def reload_config(self):
        pass

    def on_ws_focus(self, i3, event):
        self.name = event.current.name
        self.ws_event.set()

    def idle_wait(self):
        while True:
            if self.ws_event.wait(timeout=0.01):
                break
            if self.req_event.wait(timeout=0.01):
                break
        return True

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.addr, self.port))
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
                    elif 'idle' in data.decode():
                        while True:
                            if self.idle_wait():
                                current_conn.shutdown(1)
                                current_conn.close()
                                self.ws_event.clear()
                                self.req_event.clear()
                                raise BreakoutException
                    elif 'ws' in data.decode():
                        current_conn.send(self.name.encode())
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'ns list' in data.decode():
                        ns_instance = nsd.ns()
                        output = []
                        for k in ns_instance.cfg:
                            output.append(k)
                        current_conn.send(
                            bytes(
                                str(output), 'UTF-8'
                            )
                        )
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
            except BreakoutException:
                pass


if __name__ == "__main__":
    srv = i3info()
    Thread(target=srv.listen, daemon=True).start()
    Thread(
        target=srv.i3.main,
        daemon=False
    ).start()

