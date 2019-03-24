""" Menu manager module.

    This module is about creating various menu.

    For now it contains following menus:
        - Goto workspace.
        - Attach to workspace.
        - Add window to named scratchpad or circle group.
        - xprop menu to get X11-atom parameters of selected window.
        - i3-cmd menu with autocompletion.
"""

import json
import socket
import re
import subprocess
import sys
import pulsectl
from singleton import Singleton
from modi3cfg import modi3cfg
from main import i3path, get_screen_resolution
from functools import partial
from typing import List, Callable, Optional


class menu(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None) -> None:
        # Initialize modi3cfg.
        modi3cfg.__init__(self, i3)

        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3

        # i3 path used to get "send" binary path
        self.i3_path = i3path()

        # i3-msg application name
        self.i3cmd = self.conf("i3cmd")

        # magic pie to spawn error, used for autocomplete.
        self.magic_pie = self.conf('magic_pie')

        # default echo server host
        self.host = self.conf("host")

        # default echo server port
        self.port = int(self.conf("port"))

        # create echo server socket
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        # negi3mods which allows add / delete property.
        # For example this feature can be used to move / delete window
        # to / from named scratchpad.
        self.possible_mods = ['ns', 'circle']

        # Window properties shown by xprop menu.
        self.xprops_list = self.conf("xprops_list")

        # Window properties used by i3 to match windows.
        self.i3rules_xprop = set(self.conf("rules_xprop"))

        self.wslist = self.conf("wslist")

        # Magic delimiter used by add_prop / del_prop routines.
        self.delim = "@"

        # cache screen width
        self.screen_width = get_screen_resolution()["width"]

        # set up settings for rofi, dmenu, whatever
        self.launcher_font = self.conf("font") + " " + \
            str(self.conf("font_size"))
        self.location = self.conf("location")
        self.anchor = self.conf("anchor")
        self.matching = self.conf("matching")
        self.prompt = self.conf("prompt")

        self.scratchpad_color = self.conf("scratchpad_color")
        self.ws_name_color = self.conf("ws_name_color")
        self.wm_class_color = self.conf("wm_class_color")

        self.lhs_br = self.conf('left_bracket')
        self.rhs_br = self.conf('right_bracket')

        self.gap = self.conf('gap')

        self.pulse = pulsectl.Pulse('neg-pulse-selector')

    def rofi_args(self, prompt: str = None, cnum: int = 16,
                  lnum: int = 2,
                  width: Optional[int] = None,
                  markup_rows: Optional[str] = None,
                  auto_selection="-no-auto-selection") -> List[str]:
        prompt = prompt or self.prompt
        width = width or self.screen_width - 20
        markup_rows = markup_rows or '-no-markup-rows'

        """ Returns arguments list for rofi runner.

        Args:
            prompt (str): rofi prompt, optional.
            cnum (int): number of columns, optional.
            lnum (int): number of lines, optional.
            width (int): width of rofi menu, optional.
            markup_rows (str): markup rows setting.
        """
        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(cnum), '-lines', str(lnum),
            '-disable-history',
            auto_selection,
            markup_rows,
            '-p', prompt,
            '-i',  # non case-sensitive
            '-matching', f'{self.matching}',
            '-theme-str', f'* {{ font: "{self.launcher_font}"; }}',
            '-theme-str', f'#window {{ width:{width}; y-offset: -{self.gap}; \
            location: {self.location}; \
            anchor: {self.anchor}; }}',
        ]

    def i3_cmds(self) -> List[str]:
        """ Return the list of i3 commands with magic_pie hack autocompletion.
        """
        try:
            out = subprocess.run(
                [self.i3cmd, self.magic_pie],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            ).stdout
        except Exception:
            return []

        lst = [
            t.replace("'", '')
            for t in re.split('\\s*,\\s*', json.loads(
                out.decode('UTF-8')
            )[0]['error'])[2:]
        ]

        lst.remove('nop')
        lst.append('splitv')
        lst.append('splith')
        lst.sort()

        return lst

    def switch(self, args: List) -> None:
        """ Defines pipe-based IPC for nsd module. With appropriate function
            bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "run": self.i3_cmd_menu,
            "xprop": self.xprop_menu,
            "pls": self.pulseaudio_menu,
            "autoprop": self.autoprop,
            "show_props": self.show_props,
            "ws": self.goto_ws,
            "goto_win": self.goto_win,
            "attach": self.attach_win,
            "movews": self.move_to_ws,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def win_act_simple(self, cmd: str, prompt: str) -> None:
        """ Run simple and fast selection dialog for window with given action.
            Args:
                cmd (str): action for window to run.
                prompt (str): custom prompt for rofi.
        """
        leaves = self.i3.get_tree().leaves()
        winlist = [win.name for win in leaves]
        winlist_len = len(winlist)
        if winlist and winlist_len > 1:
            win_name = subprocess.run(
                self.rofi_args(
                    cnum=winlist_len,
                    width=int(self.screen_width * 0.75),
                    prompt=f"{prompt} {self.prompt}"
                ),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(winlist), 'UTF-8')
            ).stdout
        elif winlist_len:
            win_name = winlist[0].encode()

        if win_name is not None and win_name:
            win_name = win_name.decode('UTF-8').strip()
            for w in leaves:
                if w.name == win_name:
                    w.command(cmd)

    def win_act_pretty(self, cmd: str, prompt: str) -> None:
        """ Run beautiful selection dialog for window with given action
            Args:
                cmd (string): action for window to run.
                prompt (string): custom prompt for rofi.
        """
        tree = self.i3.get_tree()
        leaves = tree.leaves()
        focused = tree.find_focused()

        winlist, scratchlist, wlist = [], [], []
        for win in leaves:
            if win.id != focused.id:
                ws_name = win.parent.parent.name
                if ws_name == '__i3_scratch':
                    ws_name = self.colorize(
                        ' scratchpad', self.scratchpad_color
                    )
                    scratchlist.append(
                        f'{ws_name:<58} {self.colorize(win.window_class, "{self.wm_class_color}"):<64} {re.sub("<[^<]+?>", "", win.name)}'
                    )
                else:
                    ws_name = self.colorize(ws_name, self.ws_name_color)
                    wlist.append(
                        f'{ws_name:<58} {self.colorize(win.window_class, "{self.wm_class_color}"):<64} {re.sub("<[^<]+?>", "", win.name)}'
                    )
        winlist = wlist + scratchlist

        winlist_len = len(winlist)
        if winlist and winlist_len > 1:
            win_name = subprocess.run(
                self.rofi_args(
                    lnum=winlist_len,
                    width=int(self.screen_width * 0.75),
                    prompt=f"{prompt} {self.prompt}",
                    markup_rows='-markup-rows'
                ),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(winlist), 'UTF-8')
            ).stdout
        elif winlist_len:
            win_name = winlist[0]

        if win_name is not None and win_name:
            win_name = win_name.decode('UTF-8').strip()
            for w in leaves:
                if w.name in win_name:
                    w.command(cmd)

    def colorize(self, s: str,
                 color: str, weight: str = 'normal') -> str:
        return f"<span weight='{weight}' color='{color}'>{s}</span>"

    def wrap_str(self, s: str) -> str:
        return self.lhs_br + s + self.rhs_br

    def goto_win(self) -> None:
        """ Run rofi goto selection dialog
        """
        self.win_act_simple('focus', self.wrap_str('go'))

    def attach_win(self) -> None:
        """ Attach window to the current workspace.
        """
        self.win_act_simple(
            'move window to workspace current', self.wrap_str('attach')
        )

    def show_props(self) -> None:
        """ Send notify-osd message about current properties.
        """
        aprop_str = self.get_autoprop_as_str(with_title=False)
        notify_msg = ['notify-send', 'X11 prop', aprop_str]
        subprocess.run(notify_msg)

    def i3_cmd_args(self, cmd: str) -> List[str]:
        try:
            out = subprocess.run(
                [self.i3cmd, cmd],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            ).stdout
            if out is not None:
                ret = [
                    t.replace("'", '') for t in
                    re.split('\\s*, \\s*', json.loads(
                                out.decode('UTF-8')
                            )[0]['error'])[1:]
                ]
            return ret
        except Exception:
            return None

    def pulseaudio_menu(self):
        rofi_app_list = []
        rofi_output_list = []

        pulse_app_settings = {}

        pulse_sink_list = self.pulse.sink_list()
        pulse_app_list = self.pulse.sink_input_list()

        for t in pulse_app_list:
            app_name = t.proplist["media.name"] + ' -- ' + \
                t.proplist["application.name"]
            rofi_app_list += [app_name]
            pulse_app_settings[app_name] = t

        if len(rofi_app_list) > 0:
            rofi_output_list, app_ret = self.pulseaudio_select_app(
                rofi_app_list, pulse_app_settings, pulse_sink_list
            )
            if len(rofi_output_list) > 0:
                self.pulseaudio_select_output(
                    rofi_output_list, pulse_app_settings, app_ret)

    def pulseaudio_select_app(self, rofi_app_list, pulse_app_settings,
                              pulse_sink_list) -> (List[str], str):
        rofi_app_sel = subprocess.run(
            self.rofi_args(
                cnum=1,
                lnum=len(rofi_app_list),
                auto_selection='-auto-select',
                width=int(self.screen_width * 0.55),
                prompt=f'{self.wrap_str("pulse app")} {self.prompt}',
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(rofi_app_list), 'UTF-8')
        ).stdout

        if rofi_app_sel is not None:
            app_ret = rofi_app_sel.decode('UTF-8').strip()

        exclude_device_name = ""
        sel_app_props = pulse_app_settings[app_ret].proplist
        for t in self.pulse.stream_restore_list():
            if t is not None:
                if t.device is not None:
                    if t.name == sel_app_props['module-stream-restore.id']:
                        exclude_device_name = t.device

        rofi_output_list = []
        for n, t in enumerate(pulse_sink_list):
            if t.proplist.get('udev.id', ''):
                if t.proplist['udev.id'].split('.')[0] == \
                        exclude_device_name.split('.')[1]:
                    continue
            if t.proplist.get('device.profile.name', ''):
                if t.proplist['device.profile.name'] == \
                        exclude_device_name.split('.')[-1]:
                    continue
            rofi_output_list += [str(t.index) + ' -- ' + t.description]

        return rofi_output_list, app_ret

    def pulseaudio_select_output(
            self, rofi_output_list, pulse_app_settings, app_ret) -> None:
        rofi_output_sel = subprocess.run(
            self.rofi_args(
                cnum=1,
                lnum=len(rofi_output_list),
                auto_selection='-auto-select',
                width=int(self.screen_width * 0.55),
                prompt=f'{self.wrap_str("pulse output")} {self.prompt}'
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(rofi_output_list), 'UTF-8')
        ).stdout

        if rofi_output_sel is not None:
            out_ret = rofi_output_sel.decode('UTF-8').strip()

        target_idx = out_ret.split('--')[0].strip()
        if int(pulse_app_settings[app_ret].index) is not None \
                and int(target_idx) is not None:
            self.pulse.sink_input_move(
                int(pulse_app_settings[app_ret].index),
                int(target_idx),
            )

    def xprop_menu(self) -> None:
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
            self.rofi_args(
                cnum=1,
                lnum=len(xprops),
                width=int(self.screen_width * 0.75),
                prompt=f'{self.wrap_str("xprop")} {self.prompt}'
            ),
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

    def get_autoprop_as_str(self, with_title: bool = False,
                            with_role: bool = False) -> str:
        """ Convert xprops list to i3 commands format.

        Args:
            with_title (bool): add WM_NAME attribute, to the list, optional.
            with_role (bool): add WM_WINDOW_ROLE attribute to the list,
            optional.
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
        for attr in self.i3rules_xprop:
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

    def mod_data_list(self, mod: str) -> List[str]:
        """ Extract list of module tags. Used by add_prop menus.

        Args:
            mod (str): negi3mod name.
        """
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.send(bytes(f'{mod}_list\n', 'UTF-8'))

        out = self.sock.recv(1024)

        self.sock.shutdown(1)
        self.sock.close()

        lst = []
        if out is not None:
            lst = out.decode('UTF-8').strip()[1:-1].split(', ')
            lst = [t.replace("'", '') for t in lst]

        return lst

    def tag_name(self, mod: str, lst: List[str]) -> str:
        """ Returns tag name, selected by rofi.

        Args:
            mod (str): module name string.
            lst (List[str]): list of rofi input.
        """
        rofi_tag = subprocess.run(
            self.rofi_args(
                cnum=len(lst),
                width=int(self.screen_width * 0.75),
                prompt=f'{self.wrap_str(mod)} {self.prompt}'
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(lst), 'UTF-8')
        ).stdout

        if rofi_tag is not None and rofi_tag:
            return rofi_tag.decode('UTF-8').strip()

    def get_mod(self) -> str:
        """ Select negi3mod for add_prop by rofi.
        """
        mod = subprocess.run(
            self.rofi_args(
                cnum=len(self.possible_mods),
                lnum=1,
                width=int(self.screen_width * 0.75),
                prompt=f'{self.wrap_str("selmod")} {self.prompt}'
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(self.possible_mods), 'UTF-8')
        ).stdout

        if mod is not None and mod:
            return mod.decode('UTF-8').strip()
        else:
            return ""

    def autoprop(self) -> None:
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
                cmdl = [
                    f'{self.i3_path}send',
                    f'{mod}', 'add_prop',
                    f'{tag_name}', f'{aprop_str}'
                ]
                subprocess.run(cmdl)
        else:
            print(f'No tag name specified for props [{aprop_str}]')

    def select_ws(self, use_wslist: bool) -> str:
        """ Apply target function to workspace.
        """
        if use_wslist:
            wslist = self.wslist
        else:
            wslist = [ws.name for ws in self.i3.get_workspaces()] + ["[empty]"]
        ws = subprocess.run(
            self.rofi_args(
                cnum=len(wslist),
                width=int(self.screen_width * 0.66),
                prompt=f'{self.wrap_str("ws")} {self.prompt}'
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(wslist), 'UTF-8')
        ).stdout

        return ws.decode('UTF-8').strip()

    def apply_to_ws(self, ws_func: Callable) -> None:
        """ Partial apply function to workspace.
        """
        ws_func()

    def goto_ws(self, use_wslist: bool = True) -> None:
        """ Go to workspace menu.
        """
        ws = self.select_ws(use_wslist)
        if ws is not None and ws:
            self.apply_to_ws(
                partial(self.i3.command, f'workspace {ws}')
            )

    def move_to_ws(self, use_wslist: bool = True) -> None:
        """ Move current window to the selected workspace
        """
        ws = self.select_ws(use_wslist)
        if ws is not None and ws:
            self.apply_to_ws(
                partial(self.i3.command,
                        f'[con_id=__focused__] move to workspace {ws}')
            )

    def i3_cmd_menu(self) -> int:
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
                            self.rofi_args(
                                f"{self.wrap_str('i3cmd')} {self.prompt} "
                                + cmd
                            ),
                            stdout=subprocess.PIPE,
                            input=bytes('\n'.join(args), 'UTF-8')
                        ).stdout
                        cmd += ' ' + cmd_rerun.decode('UTF-8').strip()
                        prev_args = args
                    except subprocess.CalledProcessError as e:
                        return e.returncode

        if not ok:
            subprocess.run(notify_msg)

