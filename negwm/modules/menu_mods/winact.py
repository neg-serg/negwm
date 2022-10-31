#!/usr/bin/env python
import subprocess
from functools import partial
from typing import Callable
from typing import List
import i3ipc
import i3ipc.con


class winact():
    def __init__(self):
        self.prompt='❯>'
        self.matching='fuzzy'
        self.left_bracket,self.right_bracket='⟬','⟭'
        self.i3ipc=i3ipc.Connection()

    def args(self, params: dict) -> List[str]:
        """ Create run parameters to spawn rofi process from dict
            params(dict): parameters for rofi
            List(str) to do rofi subprocessing """
        prompt = self.prompt
        params['prompt'] = params.get('prompt', prompt)
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto-select'] = \
            params.get('auto-select', "-no-auto-select")
        matching = self.matching
        return [
            'rofi', '-show', '-dmenu', '-disable-history',
            params['auto-select'], params['markup_rows'],
            '-p', params['prompt'], '-i', '-matching', f'{matching}']

    def wrap_str(self, string: str) -> str:
        """ String wrapper to make it beautiful """
        return self.left_bracket + string + self.right_bracket

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
                self.args(menu_params),
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
        self.win_act_simple('focus', self.wrap_str('go'))

    def attach_win(self) -> None:
        """ Attach window to the current workspace. """
        self.win_act_simple(
            'move window to workspace current', self.wrap_str('attach')
        )

    def select_ws(self) -> str:
        """ Apply target function to workspace. """
        ws_list = list(extension.get_mods()['conf_gen'].cfg['workspaces'])
        menu_params = {'prompt': f'{self.wrap_str("ws")} {self.prompt}'}
        try:
            workspace_name = subprocess.run(
                self.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(ws_list), 'UTF-8'),
                check=False
            ).stdout
            selected_ws = workspace_name.decode('UTF-8').strip()
            if selected_ws:
                num = ws_list.index(selected_ws) + 1
                return str(f'{num} :: {selected_ws}')
        except Exception:
            return ''
        return ''

    @staticmethod
    def apply_to_ws(ws_func: Callable) -> None:
        """ Partial apply function to workspace. """
        ws_func()

    def goto_ws(self) -> None:
        """ Go to workspace menu. """
        workspace_name = self.select_ws()
        self.apply_to_ws(
            partial(self.i3ipc.command, f'workspace {workspace_name}'))

    def move_to_ws(self) -> None:
        """ Move current window to the selected workspace """
        workspace_name = self.select_ws()
        if workspace_name is not None and workspace_name:
            ws_splitname = workspace_name.split('::')
            if len(ws_splitname) > 1:
                ws_num = ws_splitname[0].strip()
                self.apply_to_ws(
                    partial(self.i3ipc.command,
                    f'[con_id=__focused__] move to workspace number {ws_num}')
                )

if __name__ == '__main__':
    winact().goto_ws()
    # self.ws = getattr(self, 'winact').goto_ws
    # self.goto_win = getattr(self, 'winact').goto_win
    # self.attach = getattr(self, 'winact').attach_win
    # self.movews = getattr(self, 'winact').move_to_ws
