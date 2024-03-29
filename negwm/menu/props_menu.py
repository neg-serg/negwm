#!/usr/bin/env python
import subprocess
import re
import socket
import logging
import asyncio
import pickle
import sys
from typing import List
import i3ipc
import i3ipc.con

from negwm.modules.reflection import reflection

class menu():
    @staticmethod
    def args(P: dict, prompt='❯>') -> List[str]:
        """ Create run parameters to spawn menu process from dict
            P(dict): parameters for menu
            List(str) to do menu subprocessing """
        return [
            'rofi', 
            '-show',
            '-dmenu',
            '-disable-history',
            '-auto-select',
            '-markup-rows',
            '-p', P.get('prompt', prompt),
            '-i',
            '-matching', 'glob'
        ]

    @staticmethod
    def wrap_str(s: str, lfs='⟬', rhs='⟭') -> str:
        """ String wrapper to make it beautiful """
        return f'{lfs}{s}{rhs}'

class props():
    def __init__(self):
        self.delim="@" # Magic delimiter used by add_prop / del_prop routines.
        # create echo server socket
        self.sock=socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # negwm which allows add / delete property.
        # For example this feature can be used to move / delete window
        # to / from named scratchpad.
        self.possible_mods=['scratchpad', 'circle']
        # Window properties used by i3 to match windows.
        rules_xprop=['WM_CLASS', 'WM_WINDOW_ROLE', 'WM_NAME', '_NET_WM_NAME']
        self.prompt,self.matching='❯>','fuzzy'
        self.xprops_list=[
            'WM_CLASS', 'WM_NAME', 'WM_WINDOW_ROLE', 'WM_TRANSIENT_FOR',
            '_NET_WM_WINDOW_TYPE', '_NET_WM_STATE', '_NET_WM_PID'
        ]
        self.i3rules_xprop=set(rules_xprop)
        self.i3=i3ipc.Connection()

    def select(self, name, lst) -> str:
        """ Select extension for add_prop by menu. """
        menu_params = {'prompt': f'{menu.wrap_str(name)}' f'{self.prompt}'}
        prop = subprocess.run(
            menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(lst), 'UTF-8'),
            check=False
        ).stdout
        if prop is not None and prop:
            return prop.decode('UTF-8').strip()
        return ""

    async def move_window(self):
        """ Start autoprop menu to move current module to smth. """
        all_props = {}
        for mod in self.possible_mods:
            if mod is None or not mod:
                return
            echo=reflection.echo
            mod_cfg = pickle.loads(await echo(f'{mod} get_config\n'))
            if mod_cfg is not None and mod_cfg:
                all_props |= {k: f'{mod}@{k}' for (k,_) in mod_cfg.items()}
        prop = self.select('props', all_props.values())
        aprop_str=self.get_autoprop_as_str(with_title=False)
        if prop is not None and prop:
            try:
                p=prop.split('@')
                await reflection.run(f'{p[0]} add_prop {p[1]} {aprop_str}')
            except:
                logging.error(f'No tag name specified for props {aprop_str}')

    async def unmove_window(self):
        """ Start autoprop menu to move current module to smth. """
        all_added_props = []
        for mod in self.possible_mods:
            if mod is None or not mod:
                return
            echo=reflection.echo
            added_props = pickle.loads(await echo(f'{mod} get_added_props\n'))
            if added_props is not None and added_props:
                all_added_props.append(added_props)
        aprop_str=self.get_autoprop_as_str(with_title=False)
        drop_list = []

        for prop_list in filter(len, all_added_props):
            if prop_list and prop_list[0]:
                for props in prop_list:
                    if aprop_str == props['prop']:
                        drop_list.append((props['mod'] + '###' + props['tag']))
        if drop_list:
            tag_to_remove = self.select('remove from', drop_list)
            if tag_to_remove is not None and tag_to_remove:
                p=tag_to_remove.split('###')
                print(f'{p[0]} del_prop {p[1]} {aprop_str}')
                await reflection.run(f'{p[0]} del_prop {p[1]} {aprop_str}')
            else:
                logging.error(f'No tag name specified for props {aprop_str}')

    def show_props(self) -> None:
        """ Send notify-osd message about current properties. """
        aprop_str=self.get_autoprop_as_str(with_title=False)
        notify_msg=['notify-send', 'X11 prop', aprop_str]
        subprocess.run(notify_msg, check=False)

    def get_autoprop_as_str(self, with_title: bool=False,
                            with_role: bool=False) -> str:
        """ Convert xprops list to i3 commands format.
            with_title (bool): add WM_NAME attribute, to the list, optional.
            with_role (bool): add WM_WINDOW_ROLE attribute to the list,
            optional. """
        xprops=[]
        win=self.i3.get_tree().find_focused()
        xprop=subprocess.run(
            ['xprop', '-id', str(win.window)] + self.xprops_list,
            stdout=subprocess.PIPE,
            check=False
        ).stdout
        if xprop is not None:
            xprop=xprop.decode('UTF-8').split('\n')
        ret=[]
        for attr in self.i3rules_xprop:
            for xattr in xprop:
                xprops.append(xattr)
                if attr in xattr and 'not found' not in xattr:
                    founded_attr=re.search("[A-Z]+(.*)=", xattr).group(0)
                    xattr=re.sub("[A-Z]+(.*)=", '', xattr).split(', ')
                    if "WM_CLASS" in founded_attr:
                        for num, pr in enumerate(['instance', 'class']):
                            if xattr[num] is not None and xattr[num]:
                                ret.append(f'{pr}={xattr[num].strip()}{self.delim}')
                    if with_role and "WM_WINDOW_ROLE" in founded_attr:
                        ret.append(f'window_role={xattr[0]}{self.delim}')
                    if with_title and "WM_NAME" in founded_attr:
                        ret.append(f'title={xattr[0]}{self.delim}')
        return "[" + ''.join(sorted(ret)) + "]"

def main():
    if len(sys.argv) < 2:
        asyncio.run(props().move_window())
    else:
        match sys.argv[1]:
            case 'show': props().show_props()
            case 'del': asyncio.run(props().unmove_window())

if __name__ == '__main__':
    main()
