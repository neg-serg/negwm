import subprocess
import re
import socket
from typing import List


class props():
    def __init__(self, menu):
        self.menu = menu

        # Magic delimiter used by add_prop / del_prop routines.
        self.delim = "@"

        # default echo server host
        self.host = self.menu.conf("host")

        # default echo server port
        self.port = int(self.menu.conf("port"))

        # create echo server socket
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        # negi3mods which allows add / delete property.
        # For example this feature can be used to move / delete window
        # to / from named scratchpad.
        self.possible_mods = ['ns', 'circle']

        # Window properties used by i3 to match windows.
        self.i3rules_xprop = set(self.menu.conf("rules_xprop"))

    def tag_name(self, mod: str, lst: List[str]) -> str:
        """ Returns tag name, selected by menu.

        Args:
            mod (str): module name string.
            lst (List[str]): list of menu input.
        """
        menu_params = {
            'cnum': len(lst),
            'width': int(self.menu.screen_width * 0.75),
            'prompt': f'{self.menu.wrap_str(mod)} {self.menu.conf("prompt")}',
        }
        menu_tag = subprocess.run(
            self.menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(lst), 'UTF-8'),
            check=False
        ).stdout

        if menu_tag is not None and menu_tag:
            return menu_tag.decode('UTF-8').strip()

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
                    f'{self.menu.i3_path}send',
                    f'{mod}', 'add_prop',
                    f'{tag_name}', f'{aprop_str}'
                ]
                subprocess.run(cmdl, check=False)
        else:
            print(f'No tag name specified for props [{aprop_str}]')

    def get_mod(self) -> str:
        """ Select negi3mod for add_prop by menu.
        """
        menu_params = {
            'cnum': len(self.possible_mods),
            'lnum': 1,
            'width': int(self.menu.screen_width * 0.75),
            'prompt': f'{self.menu.wrap_str("selmod")} \
            {self.menu.conf("prompt")}'
        }
        mod = subprocess.run(
            self.menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(self.possible_mods), 'UTF-8'),
            check=False
        ).stdout

        if mod is not None and mod:
            return mod.decode('UTF-8').strip()

        return ""

    def show_props(self) -> None:
        """ Send notify-osd message about current properties.
        """
        aprop_str = self.get_autoprop_as_str(with_title=False)
        notify_msg = ['notify-send', 'X11 prop', aprop_str]
        subprocess.run(notify_msg, check=False)

    def get_autoprop_as_str(self, with_title: bool = False,
                            with_role: bool = False) -> str:
        """ Convert xprops list to i3 commands format.

        Args:
            with_title (bool): add WM_NAME attribute, to the list, optional.
            with_role (bool): add WM_WINDOW_ROLE attribute to the list,
            optional.
        """
        xprops = []
        win = self.menu.i3ipc.get_tree().find_focused()
        xprop = subprocess.run(
            ['xprop', '-id', str(win.window)] + self.menu.xprops_list,
            stdout=subprocess.PIPE,
            check=False
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
                        if xattr[0] is not None and xattr[0]:
                            ret.append(f'instance={xattr[0]}{self.delim}')
                        if xattr[1] is not None and xattr[1]:
                            ret.append(f'class={xattr[1]}{self.delim}')
                    if with_role and "WM_WINDOW_ROLE" in founded_attr:
                        ret.append(f'window_role={xattr[0]}{self.delim}')
                    if with_title and "WM_NAME" in founded_attr:
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

