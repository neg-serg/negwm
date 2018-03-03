#!/usr/bin/env python3
import socket
import i3ipc
import os
import re
import select
import selectors
from singleton import Singleton
from cfg_master import CfgMaster

from nsd import ns
from circled import circle


class BreakoutException(Exception):
    pass


class WaitableEvent:
    # Provides an abstract object that can be used to resume select loops with
    # indefinite waits from another thread or process. This mimics the standard
    # threading.Event interface.

    # taken from [https://lat.sk/2015/02/multiple-event-waiting-python-3/]

    def __init__(self):
        self._read_fd, self._write_fd = os.pipe()

    def wait(self, timeout=None):
        rfds, wfds, efds = select.select([self._read_fd], [], [], timeout)
        return self._read_fd in rfds

    def isSet(self):
        return self.wait(0)

    def clear(self):
        if self.isSet():
            os.read(self._read_fd, 1)

    def set(self):
        if not self.isSet():
            os.write(self._write_fd, b'1')

    def fileno(self):
        # Return the FD number of the read side of the pipe, allows this object
        # to be used with select.select().
        return self._read_fd

    def __del__(self):
        os.close(self._read_fd)
        os.close(self._write_fd)


class i3info(CfgMaster):
    __metaclass__ = Singleton

    def __init__(self):
        super().__init__()
        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.i3.on('binding', self.on_binding_event)

        self.addr = self.cfg["addr"]
        self.port = int(self.cfg["port"])
        self.ws_name = ""
        self.binding_mode = ""
        self.mode_regex = re.compile('.*mode ')
        self.split_by = re.compile('[;,]')

        self.ns_instance = ns()
        self.circle_instance = circle()

        self.sel = selectors.DefaultSelector()

        self.ws_event = WaitableEvent()
        self.req_event = WaitableEvent()
        self.binding_event = WaitableEvent()

        for ws in self.i3.get_workspaces():
            if ws.focused:
                self.ws_name = ws.name
                if not self.ws_name[0].isalpha():
                    self.ws_name = self.colorize(
                        self.ws_name[0], color="#8FA8C7"
                    ) + self.ws_name[1:]
                self.ws_event.set()
                break

        self.sel.register(
            self.ws_event,
            selectors.EVENT_READ,
            "ws event"
        )
        self.sel.register(
            self.req_event,
            selectors.EVENT_READ,
            "req event"
        )
        self.sel.register(
            self.binding_event,
            selectors.EVENT_READ,
            "binding event"
        )

    def switch(self, args):
        {
            "request": self.request,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def request(self):
        self.req_event.set()

    def reload_config(self):
        pass

    def on_ws_focus(self, i3, event):
        self.ws_name = event.current.name
        if not self.ws_name[0].isalpha():
            self.ws_name = self.colorize(
                self.ws_name[0], color="#8FA8C7"
            ) + self.ws_name[1:]
        self.ws_event.set()

    def colorize(self, s, color="#005fd7"):
        return f"%{{F{color}}}{s}%{{F#ccc}}"

    def on_binding_event(self, i3, event):
        bind_cmd = event.binding.command
        for t in re.split(self.split_by, bind_cmd):
            if 'mode' in t:
                ret = re.sub(self.mode_regex, '', t)
                if ret[0] == ret[-1] and ret[0] in {'"',"'"}:
                    ret = ret[1:-1]
                    if ret == "default":
                        self.binding_mode = ''
                    else:
                        self.binding_mode = self.colorize(ret) + ' '
        self.binding_event.set()

    def idle_wait(self):
        for ev in self.sel.select():
            pass
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
                                raise BreakoutException
                    elif 'ws' in data.decode():
                        current_conn.send((self.binding_mode + self.ws_name).encode())
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'ns_list' in data.decode():
                        output = []
                        for k in self.ns_instance.cfg:
                            output.append(k)
                        current_conn.send(
                            bytes(str(output), 'UTF-8')
                        )
                        break
                    elif 'circle_list' in data.decode():
                        output = []
                        for k in self.circle_instance.cfg:
                            output.append(k)
                        current_conn.send(
                            bytes(str(output), 'UTF-8')
                        )
                        break
            except BreakoutException:
                pass

