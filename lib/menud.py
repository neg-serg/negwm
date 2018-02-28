#!/usr/bin/python3
import json
import re
import subprocess
import sys
import i3ipc
from singleton import Singleton


class menu():
    __metaclass__ = Singleton

    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3cmd = 'i3-msg'
        self.magic_pie = 'sssssnake'
        self.need_xprops = [
            "WM_CLASS",
            "WM_NAME",
            "WM_WINDOW_ROLE",
            "WM_TRANSIENT_FOR",
            "_NET_WM_WINDOW_TYPE",
            "_NET_WM_STATE",
            "_NET_WM_PID"
        ]

        self.i3rule_xprops = {
            "WM_CLASS",
            "WM_WINDOW_ROLE",
            "WM_NAME",
            "_NET_WM_NAME"
        }

    def rofi_args(self, prompt=">>", cnum=16, lnum=2, width=1900):
        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(cnum), '-lines', str(lnum),
            '-disable-history',
            '-p', prompt,
            '-nocase-sensitive',
            '-matching', 'fuzzy',
            '-theme-str', '* { font: "Iosevka Term Medium 14"; }',
            '-theme-str', f'#window {{ width:{width}; y-offset: -32; \
            location: south; anchor: south; }}',
        ]

    def i3_cmds(self):
        try:
            p = subprocess.Popen(
                [self.i3cmd, self.magic_pie],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )

            lst = [t.replace("'", '') for t in re.split('\s*,\s*', json.loads(
                p.communicate()[0]
            )[0]['error'])[2:]]

            p.wait()

            lst.remove('nop')
            lst.append('splitv')
            lst.append('splith')
            lst.sort()

            return lst
        except:
            return ""

    def reload_config(self):
        self.__init__()

    def switch(self, args):
        {
            "run": self.cmd_menu,
            "xprop": self.xprop_menu,
            "autoprop": self.autoprop,
            "ws": self.workspaces,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def i3_cmd_args(self, cmd):
        try:
            p = subprocess.Popen(
                ['i3-msg', cmd],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            ret = [t.replace("'", '') for t in
                re.split('\s*, \s*',json.loads(
                        p.communicate()[0]
                    )[0]['error']
                )[1:]
            ]
            p.wait()
            return ret
        except:
            return None

    def xprop_menu(self):
        xprops = []
        w = self.i3.get_tree().find_focused()
        xprop = subprocess.check_output(
            ['xprop', '-id', str(w.window)] + self.need_xprops
        ).decode().split('\n')
        for line in xprop:
            if 'not found' not in line:
                xprops.append(line)

        p = subprocess.Popen(
            self.rofi_args(cnum=1, lnum=len(xprops), width=900),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )

        p.stdin.write(bytes('\n'.join(xprops), 'UTF-8'))
        p_com = p.communicate()[0]
        p.wait()

        if p_com is not None:
            ret = p_com.decode('UTF-8').strip()
        p.stdin.close()

        # Copy to the clipboard
        if ret is not None:
            ret.strip()
            print(f"copy ret as {ret}")
            p = subprocess.Popen(
                ['xsel', '-i'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            p.stdin.write(bytes(ret, 'UTF-8'))
            p.communicate()[0]
            p.wait()
            p.stdin.close()

    def get_autoprop(self, with_title=False):
        xprops = []
        w = self.i3.get_tree().find_focused()
        xprop = subprocess.check_output(
            ['xprop', '-id', str(w.window)] + self.need_xprops
        ).decode().split('\n')
        ret = []
        for attr in self.i3rule_xprops:
            for xattr in xprop:
                xprops.append(xattr)
                if attr in xattr and 'not found' not in xattr:
                    founded_attr = re.search("[A-Z]+(.*) = ", xattr).group(0)
                    xattr = re.sub("[A-Z]+(.*) = ", '', xattr).split(', ')
                    if "WM_CLASS" in founded_attr:
                        if xattr[0] is not None and len(xattr[0]):
                            ret.append(f'class={xattr[0]} ')
                        if xattr[1] is not None and len(xattr[1]):
                            ret.append(f'instance={xattr[1]} ')
                    if "WM_WINDOW_ROLE" in founded_attr:
                        ret.append(f'window_role={xattr[0]} ')
                    if with_title:
                        if "WM_NAME" in founded_attr:
                            ret.append(f'title={xattr[0]} ')
        return "[" + ''.join(sorted(ret)) + "]"

    def autoprop(self):
        aprop_str = self.get_autoprop(with_title=False)
        print(aprop_str)
        notify_msg = ['notify-send', 'X11 prop', aprop_str]
        subprocess.Popen(notify_msg)

    def workspaces(self):
        wslist = [ws.name for ws in self.i3.get_workspaces()]
        wslist.append("[empty]")

        p = subprocess.Popen(
            self.rofi_args(cnum=len(wslist), width=1200, prompt="[ws] >>"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        p.stdin.write(bytes('\n'.join(wslist), 'UTF-8'))
        p_com = p.communicate()[0]
        p.wait()

        if p_com is not None:
            ws = p_com.decode('UTF-8').strip()
        p.stdin.close()

        self.i3.command(f'workspace {ws}')

    def cmd_menu(self):
        # set default menu args for supported menus
        cmd = ''

        try:
            p = subprocess.Popen(
                self.rofi_args(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            p.stdin.write(bytes('\n'.join(self.i3_cmds()), 'UTF-8'))
            p_com = p.communicate()[0]
            p.wait()
            if p_com is not None:
                cmd = p_com.decode('UTF-8').strip()
            p.stdin.close()
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

        if not cmd:
            # nothing to do
            return 0

        debug = False
        ok = False
        notify_msg = ""

        args = None
        prev_args = None
        while not (ok or args == ['<end>'] or args == []):
            if debug:
                print(f"evaluated cmd=[{cmd}] args=[{self.i3_cmd_args(cmd)}]")
            p = subprocess.Popen(
                (f"{self.i3msg} " + cmd).split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            r = json.loads(p.communicate()[0].decode('UTF-8').strip())
            result = r[0]['success']
            p.wait()
            ok = True
            if not result:
                ok = False
                notify_msg = ['notify-send', 'i3-cmd error', r[0]['error']]
                try:
                    args = self.i3_cmd_args(cmd)
                    if args == prev_args:
                        return 0
                    p = subprocess.Popen(
                        self.rofi_args(">> " + cmd),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE
                    )
                    p.stdin.write(bytes('\n'.join(args), 'UTF-8'))
                    cmd += ' ' + p.communicate()[0].decode('UTF-8').strip()
                    prev_args = args
                    p.stdin.close()
                    p.wait()
                except subprocess.CalledProcessError as e:
                    return e.returncode

        if not ok:
            subprocess.Popen(notify_msg)

