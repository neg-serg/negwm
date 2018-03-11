import socket
import re
import selectors
from singleton import Singleton
from cfg_master import CfgMaster

from nsd import ns
from circled import circle
from vold import vol
from modlib import WaitableEvent


class BreakoutException(Exception):
    pass


class info(CfgMaster):
    __metaclass__ = Singleton

    def __init__(self, i3, loop):
        super().__init__(i3)
        self.i3 = i3
        self.loop = loop
        self.i3.on('workspace::focus', self.on_ws_focus)
        self.i3.on('binding', self.on_binding_event)

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

        self.sel = selectors.DefaultSelector()

        self.ws_ev = WaitableEvent()
        self.request_ev = WaitableEvent()
        self.binding_ev = WaitableEvent()

        for ws in self.i3.get_workspaces():
            if ws.focused:
                self.ws_name = ws.name
                if not self.ws_name[0].isalpha():
                    self.ws_name = self.colorize(
                        self.ws_name[0], color=self.ws_color
                    ) + self.ws_name[1:]
                self.ws_ev.set()
                break

        self.sel.register(self.ws_ev, selectors.EVENT_READ, "workspace")
        self.sel.register(self.request_ev, selectors.EVENT_READ, "request")
        self.sel.register(self.binding_ev, selectors.EVENT_READ, "binding")

    def switch(self, args):
        {
            "request": self.request,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def request(self):
        self.request_ev.set()

    def on_ws_focus(self, i3, event):
        self.ws_name = event.current.name
        if not self.ws_name[0].isalpha():
            self.ws_name = self.colorize(
                self.ws_name[0], color="#8FA8C7"
            ) + self.ws_name[1:]
        self.ws_ev.set()

    def colorize(self, s, color="#005fd7"):
        return f"%{{F{color}}}{s}%{{F#ccc}}"

    def on_binding_event(self, i3, event):
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
        self.binding_ev.set()

    def idle_wait(self):
        for ev in self.sel.select():
            pass
        return True

    def listen(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn.bind((self.addr, self.port))
        conn.listen(self.conn_count)

        while True:
            try:
                current_conn, address = conn.accept()
                while True:
                    data = current_conn.recv(self.buf_size)
                    if data is None:
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'idle' in data.decode():
                        while True:
                            if self.idle_wait():
                                self.binding_ev.clear()
                                self.request_ev.clear()
                                self.ws_ev.clear()
                                current_conn.shutdown(1)
                                current_conn.close()
                                raise BreakoutException
                    elif 'ws' in data.decode():
                        current_conn.send((self.binding_mode + self.ws_name).encode())
                        self.ws_ev.clear()
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'ns_list' in data.decode():
                        output = []
                        for k in self.ns_instance.cfg:
                            output.append(k)
                        current_conn.send(bytes(str(output), 'UTF-8'))
                        self.request_ev.clear()
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'circle_list' in data.decode():
                        output = []
                        for k in self.circle_instance.cfg:
                            output.append(k)
                        current_conn.send(bytes(str(output), 'UTF-8'))
                        self.request_ev.clear()
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
                    elif 'v' in data.decode():
                        output = []
                        output = self.vol_instance.volume
                        current_conn.send(bytes(str(output), 'UTF-8'))
                        current_conn.shutdown(1)
                        current_conn.close()
                        break
            except BreakoutException:
                pass

