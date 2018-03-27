""" Menu manager module.

    This module is about creating various menu.

    For now it contains following menus:
        - Goto workspace.
        - Add window to named scratchpad or circle group.
        - xprop menu to get X11-atom parameters of selected window.
        - i3-cmd menu with autocompletion.
"""

import json
import socket
import re
import subprocess
import sys
import shlex
from singleton import Singleton
from modi3cfg import modi3cfg
from modlib import i3path


class menu(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None):
        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3

        # i3 path used to get "send" binary path
        self.i3_path = i3path()

        # i3-msg application name
        self.i3cmd = 'i3-msg'

        # magic pie to spawn error, used for autocomplete.
        self.magic_pie = 'sssssnake'

        # default echo server host
        self.host = '0.0.0.0'

        # default echo server port
        self.port = 31888

        # create echo server socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # negi3mods which allows add / delete property.
        # For example this feature can be used to move / delete window
        # to / from named scratchpad.
        self.possible_mods = ['ns', 'circle']

        # Window properties shown by xprop menu.
        self.xprops_list = [
            "WM_CLASS",
            "WM_NAME",
            "WM_WINDOW_ROLE",
            "WM_TRANSIENT_FOR",
            "_NET_WM_WINDOW_TYPE",
            "_NET_WM_STATE",
            "_NET_WM_PID"
        ]

        # Window properties used by i3 to match windows.
        self.i3rule_xprops = {
            "WM_CLASS",
            "WM_WINDOW_ROLE",
            "WM_NAME",
            "_NET_WM_NAME"
        }

        # Magic delimiter used by add_prop / del_prop routines.
        self.delim = "@"

    def rofi_args(self, prompt=">>", cnum=16, lnum=2, width=1900):
        """ Returns arguments list for rofi runner.

        Args:
            prompt (str): rofi prompt, optional.
            cnum (int): number of columns, optional.
            lnum (int): number of lines, optional.
            width (int): width of rofi menu.
        """
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
        """ Return the list of i3 commands with magic_pie hack autocompletion.
        """
        try:
            out = subprocess.run(
                [self.i3cmd, self.magic_pie],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            ).stdout
        except:
            return ""

        lst = [
            t.replace("'", '')
            for t in re.split('\s*,\s*', json.loads(
                out.decode('UTF-8')
            )[0]['error'])[2:]
        ]

        lst.remove('nop')
        lst.append('splitv')
        lst.append('splith')
        lst.sort()

        return lst

    def switch(self, args):
        """ Defines pipe-based IPC for nsd module. With appropriate function bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "run": self.cmd_menu,
            "xprop": self.xprop_menu,
            "autoprop": self.autoprop,
            "show_props": self.show_props,
            "ws": self.goto_ws,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def show_props(self):
        """ Send notify-osd message about current properties.
        """
        aprop_str = self.get_autoprop_as_str(with_title=False)
        print(aprop_str)
        notify_msg = ['notify-send', 'X11 prop', aprop_str]
        subprocess.run(notify_msg)

    def i3_cmd_args(self, cmd):
        try:
            out = subprocess.run(
                ['i3-msg', cmd],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            ).stdout
            if out is not None:
                ret = [
                    t.replace("'", '') for t in
                    re.split('\s*, \s*', json.loads(
                                out.decode('UTF-8')
                            )[0]['error'])[1:]
                ]
            return ret
        except:
            return None

    def xprop_menu(self):
        """ Menu to show X11 atom attributes for current window.
        """
        xprops = []
        w = self.i3.get_tree().find_focused()
        xprop = subprocess.run(
            ['xprop', '-id', str(w.window)] + self.xprops_list,
            stdout=subprocess.PIPE
        ).stdout
        if xprop is not None:
            xprop = xprop.decode().split('\n')
            for line in xprop:
                if 'not found' not in line:
                    xprops.append(line)

        xprop_sel = subprocess.run(
            self.rofi_args(cnum=1, lnum=len(xprops), width=900),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(xprops), 'UTF-8')
        ).stdout

        if xprop_sel is not None:
            ret = xprop_sel.decode('UTF-8').strip()

        # Copy to the clipboard
        if ret is not None and ret != '':
            subprocess.run(
                ['xsel', '-i'],
                input=bytes(ret.strip(), 'UTF-8')
            )

    def get_autoprop_as_str(self, with_title=False, with_role=False):
        """ Convert xprops list to i3 commands format.

        Args:
            with_title (bool): add WM_NAME attribute, to the list, optional.
            with_role (bool): add WM_WINDOW_ROLE attribute to the list, optional.
        """
        xprops = []
        w = self.i3.get_tree().find_focused()
        xprop = subprocess.run(
            ['xprop', '-id', str(w.window)] + self.xprops_list,
            stdout=subprocess.PIPE
        ).stdout
        if xprop is not None:
            xprop = xprop.decode('UTF-8').split('\n')
        ret = []
        for attr in self.i3rule_xprops:
            for xattr in xprop:
                xprops.append(xattr)
                if attr in xattr and 'not found' not in xattr:
                    founded_attr = re.search("[A-Z]+(.*) = ", xattr).group(0)
                    xattr = re.sub("[A-Z]+(.*) = ", '', xattr).split(', ')
                    if "WM_CLASS" in founded_attr:
                        if xattr[0] is not None and len(xattr[0]):
                            ret.append(f'instance={xattr[0]}{self.delim}')
                        if xattr[1] is not None and len(xattr[1]):
                            ret.append(f'class={xattr[1]}{self.delim}')
                    if with_role:
                        if "WM_WINDOW_ROLE" in founded_attr:
                            ret.append(f'window_role={xattr[0]}{self.delim}')
                    if with_title:
                        if "WM_NAME" in founded_attr:
                            ret.append(f'title={xattr[0]}{self.delim}')
        return "[" + ''.join(sorted(ret)) + "]"

    def mod_data_list(self, mod):
        """ Extract list of module tags. Used by add_prop menus.

        Args:
            mod (str): negi3mod name.
        """
        self.sock.connect((self.host, self.port))
        self.sock.send(bytes(f'{mod}_list\n', 'UTF-8'))
        out = self.sock.recv(1024)
        self.sock.close()
        lst = []
        if out is not None:
            lst = out.decode('UTF-8').strip()[1:-1].split(', ')
            lst = [t.replace("'", '') for t in lst]

        return lst

    def tag_name(self, mod, lst):
        """ Returns tag name, selected by rofi.

        Args:
            mod (str): module name string.
            lst (List): list of rofi input.
        """
        rofi_tag = subprocess.run(
            self.rofi_args(
                cnum=len(lst),
                width=1200,
                prompt=f"[{mod}] >>"
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(lst), 'UTF-8')
        ).stdout

        if rofi_tag is not None and rofi_tag:
            return rofi_tag.decode('UTF-8').strip()

    def get_mod(self):
        """ Select negi3mod for add_prop by rofi.
        """
        mod = subprocess.run(
            self.rofi_args(
                cnum=len(self.possible_mods),
                lnum=1,
                width=1200,
                prompt=f"[selmod] >>"
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(self.possible_mods), 'UTF-8')
        ).stdout

        if mod is not None and mod:
            return mod.decode('UTF-8').strip()

    def autoprop(self):
        """ Start autoprop menu to move current module to smth.
        """
        mod = self.get_mod()
        if mod is None or not mod:
            return

        aprop_str = self.get_autoprop_as_str(with_title=False)

        lst = self.mod_data_list(mod)
        tag_name = self.tag_name(mod, lst)

        if tag_name is not None and tag_name:
            for mod in self.possible_mods:
                add_prop_cmd = f'{self.i3_path}send {mod} add_prop \
                                {tag_name} {aprop_str}'
                subprocess.run(shlex.split(add_prop_cmd))
        else:
            print('[no tag name specified] for props [{aprop_str}]')

    def goto_ws(self):
        """ Go to workspace menu.
        """
        wslist = [ws.name for ws in self.i3.get_workspaces()] + ["[empty]"]
        ws = subprocess.run(
            self.rofi_args(cnum=len(wslist), width=1200, prompt="[ws] >>"),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(wslist), 'UTF-8')
        ).stdout

        if ws is not None and ws:
            ws = ws.decode('UTF-8').strip()
            self.i3.command(f'workspace {ws}')

    def cmd_menu(self):
        """ Menu for i3 commands with hackish autocompletion.
        """
        # set default menu args for supported menus
        cmd = ''

        try:
            cmd_rofi = subprocess.run(
                self.rofi_args(),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(self.i3_cmds()), 'UTF-8')
            ).stdout
            if cmd_rofi is not None and cmd_rofi:
                cmd = cmd_rofi.decode('UTF-8').strip()
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
            out = subprocess.run(
                (f"{self.i3cmd} " + cmd).split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            if out is not None and out:
                r = json.loads(out.decode('UTF-8').strip())
                result = r[0].get('success', '')
                err = r[0].get('error', '')
                ok = True
                if not result:
                    ok = False
                    notify_msg = ['notify-send', 'i3-cmd error', err]
                    try:
                        args = self.i3_cmd_args(cmd)
                        if args == prev_args:
                            return 0
                        cmd_rerun = subprocess.run(
                            self.rofi_args(">> " + cmd),
                            stdout=subprocess.PIPE,
                            input=bytes('\n'.join(args), 'UTF-8')
                        ).stdout
                        cmd += ' ' + cmd_rerun.decode('UTF-8').strip()
                        prev_args = args
                    except subprocess.CalledProcessError as e:
                        return e.returncode

        if not ok:
            subprocess.run(notify_msg)

