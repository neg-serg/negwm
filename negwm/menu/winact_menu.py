#!/usr/bin/env python
import subprocess
import sys
from functools import partial
from typing import Callable
import asyncio
import pickle
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


class winact():
    def __init__(self):
        self.prompt='❯>'
        self.i3ipc=i3ipc.Connection()

    def win_act_simple(self, cmd: str, prompt: str) -> None:
        """ Run simple and fast rofi menu for window with given action.
            Args:
                cmd (str): action for window to run.
                prompt (str): custom prompt for menu.
        """
        leaves = self.i3ipc.get_tree().leaves()
        winlist = [getattr(win,'name') for win in leaves]
        winlist_len = len(winlist)
        menu_params = {'prompt': f"{prompt} {self.prompt}"}
        win_name = None
        if winlist and winlist_len > 1:
            win_name = subprocess.run(
                menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(winlist), 'UTF-8'),
                check=False
            ).stdout
        elif winlist_len:
            win_name = winlist[0].encode()
        if win_name is not None and win_name:
            win_name = win_name.decode('UTF-8').strip()
            for win in leaves:
                if getattr(win, 'name') == win_name:
                    win.command(cmd)

    def goto_win(self) -> None:
        """ Run menu goto rofi menu """
        self.win_act_simple('focus', menu.wrap_str('go'))

    def attach_win(self) -> None:
        """ Attach window to the current workspace. """
        self.win_act_simple(
            'move window to workspace current', menu.wrap_str('attach')
        )

    async def select_ws(self) -> str:
        """ Apply target function to workspace. """
        echo = reflection.echo
        ws_list = pickle.loads(await echo(f'configurator raw_ws\n'))
        menu_params = {'prompt': f'{menu.wrap_str("ws")} {self.prompt}'}
        return_with_number = False
        try:
            workspace_name = subprocess.run(
                menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(ws_list), 'UTF-8'),
                check=False
            ).stdout
            selected_ws = workspace_name.decode('UTF-8').strip()
            if selected_ws:
                if return_with_number:
                    return f'{ws_list.index(selected_ws)+1}: {selected_ws}'
                else:
                    return str(selected_ws)
        except Exception:
            return ''
        return ''

    @staticmethod
    def apply_to_ws(ws_func: Callable) -> None:
        """ Partial apply function to workspace. """
        ws_func()

    async def goto_ws(self) -> None:
        """ Go to workspace menu. """
        ws = await self.select_ws()
        self.apply_to_ws(
            partial(self.i3ipc.command, f'workspace \"{ws}\"'))

    async def move_to_ws(self) -> None:
        """ Move current window to the selected workspace """
        workspace_name = await self.select_ws()
        if workspace_name is not None and workspace_name:
            ws = workspace_name
            self.apply_to_ws(
                partial(self.i3ipc.command,
                f'[con_id=__focused__] move to workspace \"{ws}\"')
            )

def main():
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'ws': asyncio.run(winact().goto_ws())
            case 'win': winact().goto_win()
            case 'attach': winact().attach_win()
            case 'move': asyncio.run(winact().move_to_ws())

if __name__ == '__main__':
    main()
